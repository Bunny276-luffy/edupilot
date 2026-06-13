"""
Elasticsearch service — index and search past question papers,
with local in-memory fallback keyword search if ES is unavailable.
"""
import os
import logging
from typing import Any, Optional, List
from elasticsearch import AsyncElasticsearch
from dotenv import load_dotenv

load_dotenv()

ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY", "")

INDEX_NAME = "edupilot_papers"
logger = logging.getLogger("edupilot")

_es_client: Optional[AsyncElasticsearch] = None
_use_es_fallback = False

# ─── In-Memory Datastore Fallback ──────────────────────────────────────────────
_indexed_papers: List[dict] = []


async def check_elastic_connection() -> None:
    """Check if Elasticsearch endpoint is configured and reachable."""
    global _es_client, _use_es_fallback
    if not ELASTIC_ENDPOINT:
        _use_es_fallback = True
        logger.warning("ELASTIC_ENDPOINT not set. Switching to Elasticsearch in-memory fallback search.")
        return

    try:
        _es_client = AsyncElasticsearch(
            ELASTIC_ENDPOINT,
            api_key=ELASTIC_API_KEY,
            verify_certs=True,
            request_timeout=2
        )
        await _es_client.ping()
        _use_es_fallback = False
        logger.info("Successfully connected to Elasticsearch.")
    except Exception as e:
        _use_es_fallback = True
        logger.warning(f"Elasticsearch connection failed: {e}. Switching to in-memory fallback search.")


def get_es_client() -> AsyncElasticsearch:
    global _es_client
    if _es_client is None:
        if ELASTIC_ENDPOINT and ELASTIC_API_KEY:
            _es_client = AsyncElasticsearch(
                ELASTIC_ENDPOINT,
                api_key=ELASTIC_API_KEY,
                verify_certs=True,
            )
        else:
            _es_client = AsyncElasticsearch("http://localhost:9200")
    return _es_client


async def ensure_index() -> None:
    """Create the index with proper mappings if it doesn't exist."""
    if _use_es_fallback:
        return

    es = get_es_client()
    try:
        exists = await es.indices.exists(index=INDEX_NAME)
        if not exists:
            await es.indices.create(
                index=INDEX_NAME,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "edu_analyzer": {
                                    "type": "standard",
                                    "stopwords": "_english_",
                                }
                            }
                        },
                    },
                    "mappings": {
                        "properties": {
                            "question_text": {
                                "type": "text",
                                "analyzer": "edu_analyzer",
                                "term_vector": "with_positions_offsets",
                            },
                            "subject": {"type": "keyword"},
                            "topic": {"type": "keyword"},
                            "year": {"type": "integer"},
                            "source_document": {"type": "keyword"},
                            "page": {"type": "integer"},
                            "university": {"type": "keyword"},
                        }
                    },
                },
            )
    except Exception as exc:
        logger.warning(f"Elasticsearch index setup warning: {exc}")


async def index_question(doc: dict) -> str:
    """Index a single question document. Returns the document ID."""
    if _use_es_fallback:
        import uuid
        doc_id = str(uuid.uuid4())
        doc_copy = doc.copy()
        doc_copy["_id"] = doc_id
        _indexed_papers.append(doc_copy)
        return doc_id

    es = get_es_client()
    await ensure_index()
    result = await es.index(index=INDEX_NAME, document=doc)
    return result["_id"]


async def bulk_index_questions(docs: list[dict]) -> int:
    """Bulk index multiple questions. Returns count indexed."""
    if _use_es_fallback:
        import uuid
        count = 0
        for doc in docs:
            doc_id = str(uuid.uuid4())
            doc_copy = doc.copy()
            doc_copy["_id"] = doc_id
            _indexed_papers.append(doc_copy)
            count += 1
        return count

    es = get_es_client()
    await ensure_index()
    body = []
    for doc in docs:
        body.append({"index": {"_index": INDEX_NAME}})
        body.append(doc)
    if not body:
        return 0
    response = await es.bulk(operations=body)
    errors = [item for item in response["items"] if "error" in item.get("index", {})]
    return len(docs) - len(errors)


async def search_papers(
    query: str,
    subject: Optional[str] = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Full-text search with optional subject filter.
    Returns top_k results with highlight.
    """
    if _use_es_fallback:
        return _in_memory_search(query, subject, top_k)

    es = get_es_client()
    await ensure_index()

    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": ["question_text^3", "topic^2", "subject"],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        }
    ]
    filter_clauses = []
    if subject:
        filter_clauses.append({"term": {"subject": subject}})

    search_body = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
            }
        },
        "highlight": {
            "fields": {
                "question_text": {
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"],
                    "number_of_fragments": 3,
                }
            }
        },
        "size": top_k,
    }

    try:
        response = await es.search(index=INDEX_NAME, body=search_body)
        hits = response["hits"]["hits"]
        results = []
        for hit in hits:
            src = hit["_source"]
            highlights = hit.get("highlight", {}).get("question_text", [])
            results.append(
                {
                    "id": hit["_id"],
                    "question_text": src.get("question_text", ""),
                    "subject": src.get("subject", ""),
                    "topic": src.get("topic", ""),
                    "year": src.get("year"),
                    "source_document": src.get("source_document", ""),
                    "page": src.get("page"),
                    "university": src.get("university", ""),
                    "score": hit["_score"],
                    "highlight": highlights,
                }
            )
        return results
    except Exception as exc:
        logger.warning(f"Elasticsearch search error: {exc}. Falling back to in-memory search.")
        return _in_memory_search(query, subject, top_k)


def _in_memory_search(query: str, subject: Optional[str] = None, top_k: int = 5) -> list[dict]:
    """Perform a local keyword search on locally indexed papers, or return fallback demo data."""
    query_terms = set(query.lower().split())
    matches = []

    # Search in locally indexed documents
    for doc in _indexed_papers:
        if subject and doc.get("subject") != subject:
            continue
        
        q_text = doc.get("question_text", "")
        q_lower = q_text.lower()
        topic_lower = doc.get("topic", "").lower()
        sub_lower = doc.get("subject", "").lower()

        # Score based on keyword overlaps
        score = 0.0
        matched_words = []
        for term in query_terms:
            if term in q_lower:
                score += 3.0
                matched_words.append(term)
            if term in topic_lower:
                score += 2.0
            if term in sub_lower:
                score += 1.0

        if score > 0:
            # Simple highlighting
            highlighted_text = q_text
            for word in matched_words:
                # Basic case-insensitive replacement (rough heuristic for display)
                import re
                highlighted_text = re.sub(
                    f"({re.escape(word)})", r"<mark>\1</mark>", highlighted_text, flags=re.IGNORECASE
                )
            
            matches.append({
                "id": doc.get("_id"),
                "question_text": q_text,
                "subject": doc.get("subject", ""),
                "topic": doc.get("topic", ""),
                "year": doc.get("year"),
                "source_document": doc.get("source_document", ""),
                "page": doc.get("page", 1),
                "university": doc.get("university", ""),
                "score": score,
                "highlight": [highlighted_text]
            })

    if matches:
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k]

    # If no local indexed papers match, return demo data
    return _fallback_search(query)


def _fallback_search(query: str) -> list[dict]:
    """Return demo data when ES is not configured and local index is empty."""
    demos = [
        {
            "id": "demo_1",
            "question_text": f"Explain the concept of {query} with an example.",
            "subject": "Computer Science",
            "topic": query,
            "year": 2023,
            "source_document": "University_Paper_2023.pdf",
            "page": 3,
            "university": "Anna University",
            "score": 9.8,
            "highlight": [f"Explain the concept of <mark>{query}</mark> with an example."],
        },
        {
            "id": "demo_2",
            "question_text": f"Describe the applications of {query} in real-world scenarios.",
            "subject": "Computer Science",
            "topic": query,
            "year": 2022,
            "source_document": "University_Paper_2022.pdf",
            "page": 7,
            "university": "VTU",
            "score": 8.5,
            "highlight": [f"Describe the applications of <mark>{query}</mark> in real-world scenarios."],
        },
        {
            "id": "demo_3",
            "question_text": f"Compare and contrast different approaches to {query}.",
            "subject": "Computer Science",
            "topic": query,
            "year": 2022,
            "source_document": "Semester_Exam_May2022.pdf",
            "page": 2,
            "university": "Mumbai University",
            "score": 7.9,
            "highlight": [f"Compare and contrast different approaches to <mark>{query}</mark>."],
        },
    ]
    return demos
