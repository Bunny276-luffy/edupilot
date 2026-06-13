"""
Tool: search_papers
Delegates to Elasticsearch to search past question papers.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from services.elastic_service import search_papers


async def search_papers_tool(inputs: dict) -> dict:
    """
    Inputs:
      query (str): Natural language search query.
      subject (str, optional): Filter by subject.
      top_k (int, optional): Number of results, default 5.
    Outputs:
      dict: {results: [...]}
    """
    query = inputs.get("query", "")
    subject = inputs.get("subject")
    top_k = int(inputs.get("top_k", 5))

    if not query:
        return {"error": "query field is required"}

    results = await search_papers(query=query, subject=subject, top_k=top_k)
    return {"results": results, "count": len(results)}
