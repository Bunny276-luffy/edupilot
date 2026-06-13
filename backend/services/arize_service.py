"""
Arize Phoenix tracing service.
Stores traces in-memory, in MongoDB (phoenix_traces collection),
and locally in backend/traces/logs.json (with aiofiles or sync fallback).
"""
import os
import time
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Optional, Any, List, Dict
from collections import deque
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

ARIZE_API_KEY = os.getenv("ARIZE_API_KEY", "")
ARIZE_SPACE_KEY = os.getenv("ARIZE_SPACE_KEY", "")
ARIZE_MODEL_ID = os.getenv("ARIZE_MODEL_ID", "edupilot-gemini")

logger = logging.getLogger("edupilot")

# In-memory circular buffer — last 200 traces (fallback)
_trace_store: deque = deque(maxlen=200)

_phoenix_client = None


def init_phoenix():
    """Initialise Arize Phoenix client and OTEL tracer provider on startup."""
    global _phoenix_client
    try:
        import phoenix as px
        # Set project name in environment variable
        os.environ["PHOENIX_PROJECT_NAME"] = "edupilot-backend"
        
        # Register the tracer to send data to Phoenix
        from phoenix.otel import register
        register(project_name="edupilot-backend")
        
        # Launch the local Phoenix collector app
        px.launch_app()
        _phoenix_client = px.Client()
        logger.info("Arize Phoenix tracer initialized successfully with project 'edupilot-backend'")
    except Exception as e:
        logger.warning(f"Failed to launch Arize Phoenix: {e}")
        _phoenix_client = False


@contextmanager
def phoenix_trace(tag: str, prompt: str, model: str = "gemini-2.0-flash"):
    """
    Context manager to wrap Gemini/LLM calls in an OpenTelemetry trace span
    compatible with Arize Phoenix / OpenInference.
    """
    try:
        from opentelemetry import trace as otel_trace
        tracer = otel_trace.get_tracer("edupilot-backend")
        
        span = tracer.start_span(
            name=tag,
            attributes={
                "input.value": prompt,
                "llm.model_name": model,
            }
        )
    except Exception:
        span = None

    try:
        yield span
    except Exception as exc:
        if span:
            span.record_exception(exc)
            span.set_status(otel_trace.Status(otel_trace.StatusCode.ERROR, str(exc)))
        raise
    finally:
        if span:
            span.end()


def record_trace(
    tag: str,
    prompt: str,
    response: str,
    latency_ms: float,
    model: str = "gemini-2.0-flash",
    error: Optional[str] = None,
    token_count: Optional[int] = None,
) -> None:
    """
    Record a single LLM trace.
    1. Saves to in-memory store.
    2. Saves to MongoDB collection phoenix_traces in the background.
    3. Saves to local logs.json via aiofiles (with sync fallback) in the background.
    4. Pushes to Arize Phoenix cloud if credentials are set.
    """
    tokens = token_count or ((len(prompt) + len(response)) // 4)
    trace = {
        "id": str(uuid.uuid4()),
        "tag": tag,
        "model": model,
        "prompt": prompt[:500],           # Truncate for memory display
        "response": response[:500],
        "latency_ms": round(latency_ms, 2),
        "token_count": tokens,
        "error": error,
        "timestamp": datetime.utcnow(),
    }
    _trace_store.appendleft(trace)

    # Save to MongoDB and local JSON file asynchronously in the background
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_save_trace_to_mongo(trace))
            asyncio.create_task(_save_trace_to_file(trace))
        else:
            loop.run_until_complete(_save_trace_to_mongo(trace))
            loop.run_until_complete(_save_trace_to_file(trace))
    except Exception as e:
        logger.error(f"Failed to schedule trace background tasks: {e}")

    # Best-effort cloud push
    if ARIZE_API_KEY and ARIZE_SPACE_KEY:
        _push_to_arize(trace)


async def _save_trace_to_mongo(trace_doc: dict):
    """Save trace document to MongoDB collection 'phoenix_traces'."""
    try:
        from services.mongodb_service import get_db, _use_in_memory
        if not _use_in_memory:
            db = get_db()
            await db.phoenix_traces.insert_one(trace_doc.copy())
    except Exception as e:
        logger.error(f"Failed to save trace to MongoDB: {e}")


async def _save_trace_to_file(trace_doc: dict):
    """Save trace document to local JSON file backend/traces/logs.json using aiofiles with sync fallback."""
    try:
        import json
        log_dir = os.path.join(os.path.dirname(__file__), "..", "traces")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "logs.json")
        
        # Load existing
        traces = []
        try:
            import aiofiles
            async with aiofiles.open(log_file, mode="r", encoding="utf-8") as f:
                content = await f.read()
                if content:
                    traces = json.loads(content)
        except ImportError:
            if os.path.exists(log_file):
                with open(log_file, mode="r", encoding="utf-8") as f:
                    content = f.read()
                    if content:
                        traces = json.loads(content)
        except Exception:
            traces = []
                
        # Append and limit
        doc_copy = trace_doc.copy()
        if isinstance(doc_copy.get("timestamp"), datetime):
            doc_copy["timestamp"] = doc_copy["timestamp"].isoformat() + "Z"
            
        traces.insert(0, doc_copy)
        traces = traces[:100]  # Limit storage to last 100 traces
        
        # Write back
        try:
            import aiofiles
            async with aiofiles.open(log_file, mode="w", encoding="utf-8") as f:
                await f.write(json.dumps(traces, indent=2))
        except ImportError:
            with open(log_file, mode="w", encoding="utf-8") as f:
                f.write(json.dumps(traces, indent=2))
    except Exception as e:
        logger.error(f"Failed to save trace to logs.json file: {e}")


def _push_to_arize(trace: dict) -> None:
    """Push trace to Arize Phoenix Cloud (best-effort, non-blocking)."""
    try:
        from arize.utils.types import ModelTypes, Environments
        from arize.api import Client as ArizeClient

        client = ArizeClient(
            space_key=ARIZE_SPACE_KEY,
            api_key=ARIZE_API_KEY,
        )
        client.log(
            prediction_id=trace["id"],
            model_id=ARIZE_MODEL_ID,
            model_type=ModelTypes.GENERATIVE_LLM,
            environment=Environments.PRODUCTION,
            prompt={"prompt": trace["prompt"]},
            response={"response": trace["response"]},
            tags={
                "tag": trace["tag"],
                "latency_ms": str(trace["latency_ms"]),
                "model": trace["model"],
            },
        )
    except Exception:
        pass  # Never break main flow


async def get_recent_traces(limit: int = 20) -> list[dict]:
    """Return the most recent `limit` traces from MongoDB, falling back to local logs.json, then to in-memory."""
    # 1. Try MongoDB
    try:
        from services.mongodb_service import get_db, _use_in_memory
        if not _use_in_memory:
            db = get_db()
            cursor = db.phoenix_traces.find().sort("timestamp", -1).limit(limit)
            results = []
            async for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                if "timestamp" in doc and isinstance(doc["timestamp"], datetime):
                    doc["timestamp"] = doc["timestamp"].isoformat() + "Z"
                results.append(doc)
            return results
    except Exception as e:
        logger.error(f"Failed to query traces from MongoDB: {e}")
        
    # 2. Try Local File logs.json
    try:
        log_file = os.path.join(os.path.dirname(__file__), "..", "traces", "logs.json")
        if os.path.exists(log_file):
            try:
                import aiofiles
                async with aiofiles.open(log_file, mode="r", encoding="utf-8") as f:
                    content = await f.read()
                    if content:
                        import json
                        traces = json.loads(content)
                        return traces[:limit]
            except ImportError:
                with open(log_file, mode="r", encoding="utf-8") as f:
                    content = f.read()
                    if content:
                        import json
                        traces = json.loads(content)
                        return traces[:limit]
    except Exception as e:
        logger.error(f"Failed to read traces from logs.json file: {e}")
        
    # 3. Fallback to in-memory deque
    fallback = []
    for t in list(_trace_store)[:limit]:
        t_copy = t.copy()
        if "timestamp" in t_copy and isinstance(t_copy["timestamp"], datetime):
            t_copy["timestamp"] = t_copy["timestamp"].isoformat() + "Z"
        fallback.append(t_copy)
    return fallback
