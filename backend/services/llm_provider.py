"""
Unified LLM Provider Service — supports Mock, Ollama, OpenRouter, and Gemini,
automatically wrapped in Arize Phoenix OTEL tracing and local file logging.
"""
import os
import json
import hashlib
import struct
import random
import time
import logging
import asyncio
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger("edupilot")


class LLMProvider:
    """Base class defining the unified LLM interface with automatic tracing."""
    
    async def generate(self, prompt: str, system_prompt: str = "", tag: str = "llm_generate") -> str:
        """Generate response text for a prompt, wrapped in tracing."""
        from services.arize_service import phoenix_trace, record_trace
        model_name = getattr(self, "model", "mock-model")
        start = time.perf_counter()
        error_msg = None
        response_text = ""
        
        try:
            with phoenix_trace(tag=tag, prompt=prompt, model=model_name) as span:
                try:
                    response_text = await self._generate(prompt, system_prompt)
                    span.set_attribute("output.value", response_text[:500])
                    span.set_attribute("llm.token_count.total", (len(prompt) + len(response_text)) // 4)
                    return response_text
                except Exception as exc:
                    error_msg = str(exc)
                    span.record_exception(exc)
                    raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            record_trace(
                tag=tag,
                prompt=prompt,
                response=response_text,
                latency_ms=latency_ms,
                model=model_name,
                error=error_msg,
            )

    async def chat(self, messages: List[Dict[str, str]], system_prompt: str = "", tag: str = "llm_chat") -> str:
        """Chat with conversation history, wrapped in tracing."""
        from services.arize_service import phoenix_trace, record_trace
        model_name = getattr(self, "model", "mock-model")
        start = time.perf_counter()
        error_msg = None
        response_text = ""
        prompt_text = "\n".join(f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages)
        
        try:
            with phoenix_trace(tag=tag, prompt=prompt_text, model=model_name) as span:
                try:
                    response_text = await self._chat(messages, system_prompt)
                    span.set_attribute("output.value", response_text[:500])
                    span.set_attribute("llm.token_count.total", (len(prompt_text) + len(response_text)) // 4)
                    return response_text
                except Exception as exc:
                    error_msg = str(exc)
                    span.record_exception(exc)
                    raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            record_trace(
                tag=tag,
                prompt=prompt_text,
                response=response_text,
                latency_ms=latency_ms,
                model=model_name,
                error=error_msg,
            )

    async def _generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    async def _chat(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        raise NotImplementedError

    async def embed(self, text: str) -> List[float]:
        """Generate a 768-dimensional embedding vector."""
        raise NotImplementedError


# ─── Mock Provider ────────────────────────────────────────────────────────────

class MockProvider(LLMProvider):
    """
    Deterministic Mock Provider that requires no API keys or local servers.
    Useful for local development, testing, and datathon demonstrations.
    """
    def __init__(self):
        self.model = "mock-model-1.5"

    async def _generate(self, prompt: str, system_prompt: str = "") -> str:
        # 1. Bloom's Taxonomy Classification
        if "Bloom" in prompt or "Classify" in prompt:
            question = "Explain binary tree traversal."
            for line in prompt.splitlines():
                if "Question:" in line or "question:" in line:
                    question = line.split(":", 1)[1].strip()
                    break

            q_lower = question.lower()
            level = "Understand"
            reasoning = "The question asks for description or explanation of a concept."

            if any(k in q_lower for k in ["define", "what is", "list", "state", "name"]):
                level = "Remember"
                reasoning = "It requires recalling information or basic terms."
            elif any(k in q_lower for k in ["apply", "solve", "calculate", "compute", "use"]):
                level = "Apply"
                reasoning = "It requires applying knowledge or solving a practical problem."
            elif any(k in q_lower for k in ["analyze", "compare", "contrast", "distinguish", "differentiate"]):
                level = "Analyze"
                reasoning = "It involves examining components or comparing structures."
            elif any(k in q_lower for k in ["evaluate", "assess", "justify", "criticize"]):
                level = "Evaluate"
                reasoning = "It requires making judgments based on criteria."
            elif any(k in q_lower for k in ["design", "create", "develop", "construct", "formulate"]):
                level = "Create"
                reasoning = "It involves putting elements together to form a coherent or functional whole."

            res = {
                "question": question,
                "level": level,
                "reasoning": reasoning
            }
            return json.dumps(res)

        # 2. Bloom's suggestions
        if "higher-level" in prompt.lower() or "bloom_suggestions" in prompt.lower() or "suggest 3" in prompt.lower():
            suggestions = [
                "Design a system architecture that utilizes this concept to reduce latency by 30%.",
                "Evaluate the trade-offs of this approach compared to its alternatives under heavy workload.",
                "Formulate a mathematical proof showing the worst-case time complexity of this technique."
            ]
            return json.dumps(suggestions)

        # 3. NAAC summary
        if "naac" in prompt.lower() or "accreditation" in prompt.lower() or "attainment" in prompt.lower():
            return (
                "The academic performance analysis for this course shows a healthy attainment matrix. "
                "The Course Outcomes (COs) map directly to Program Outcomes (POs) with high correlation in analytical areas. "
                "The question distribution shows compliance with NBA guidelines, though higher-order questions can be enhanced."
            )

        # 4. Socratic Tutor
        if "socratic" in prompt.lower() or "tutor" in prompt.lower() or "topic:" in prompt.lower():
            prompt_lower = prompt.lower()

            # Extract the latest user message for keyword matching
            user_message = ""
            for line in prompt.splitlines():
                if line.strip().startswith("USER:"):
                    user_message = line.split("USER:", 1)[1].strip().lower()

            # Topic-aware Socratic responses
            if "normalization" in user_message:
                return (
                    "Interesting! Before I explain, tell me — what happens when you store the same data "
                    "in multiple places in a database? What problems might that cause?"
                    "\n\n[LEVEL: Struggling]"
                )
            elif "primary key" in user_message:
                return (
                    "Good question! Think about this — if you have a table of students, how would you "
                    "uniquely identify each student? What column would never repeat?"
                    "\n\n[LEVEL: Getting It]"
                )
            elif "algorithm" in user_message or "complexity" in user_message:
                return (
                    "Let's think step by step. If you have n items to sort, and you compare each item "
                    "to every other item, how many comparisons would that be?"
                    "\n\n[LEVEL: Getting It]"
                )
            else:
                return (
                    "That's a great starting point! Can you think of a real-world example that "
                    "illustrates this concept?"
                    "\n\n[LEVEL: Struggling]"
                )

        return "Mock response: This is a placeholder mock LLM response."

    async def _chat(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        history_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
        prompt = f"System: {system_prompt}\n\nHistory:\n{history_text}"
        return await self._generate(prompt)

    async def embed(self, text: str) -> List[float]:
        hasher = hashlib.sha256(text.encode("utf-8"))
        seed = struct.unpack("I", hasher.digest()[:4])[0]
        rng = random.Random(seed)
        vector = [rng.uniform(-1.0, 1.0) for _ in range(768)]
        norm = sum(x*x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        assert len(vector) == 768, f"Mock embedding must be 768-dim, got {len(vector)}"
        return vector


# ─── Ollama Provider ──────────────────────────────────────────────────────────

class OllamaProvider(LLMProvider):
    """Local LLM Provider via Ollama API."""
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    async def _generate(self, prompt: str, system_prompt: str = "") -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.5}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["response"]

    async def _chat(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        url = f"{self.base_url}/api/chat"
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["message"]["content"]

    async def embed(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            emb = data["embedding"]
            if len(emb) != 768:
                logger.warning(f"Ollama embedding dimension mismatch: got {len(emb)}, reshaping to 768")
                if len(emb) > 768:
                    emb = emb[:768]
                else:
                    emb = emb + [0.0] * (768 - len(emb))
            norm = sum(x*x for x in emb) ** 0.5
            if norm > 0:
                emb = [x / norm for x in emb]
            assert len(emb) == 768
            return emb


# ─── OpenRouter Provider ──────────────────────────────────────────────────────

class OpenRouterProvider(LLMProvider):
    """LLM Provider via OpenRouter API."""
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")

    async def _generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return await self._chat(messages)

    async def _chat(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/google/edupilot",
            "Content-Type": "application/json"
        }
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": self.model,
            "messages": formatted,
            "temperature": 0.5
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, text: str) -> List[float]:
        mock = MockProvider()
        return await mock.embed(text)


# ─── Gemini Provider ──────────────────────────────────────────────────────────

class GeminiProvider(LLMProvider):
    """Google Gemini Provider using google-genai SDK."""
    def __init__(self):
        from google import genai
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.client = genai.Client(api_key=self.api_key)

    async def _generate(self, prompt: str, system_prompt: str = "") -> str:
        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=0.5,
            system_instruction=system_prompt if system_prompt else None,
        )
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
        )
        return response.text

    async def _chat(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        history_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
        prompt = f"Conversation:\n{history_text}\n\nAssistant:"
        return await self._generate(prompt, system_prompt=system_prompt)

    async def embed(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
        )
        if response.embeddings and len(response.embeddings) > 0:
            emb = response.embeddings[0].values
            assert len(emb) == 768, f"Gemini embedding must be 768-dim, got {len(emb)}"
            return emb
        raise ValueError("Failed to retrieve embeddings from Gemini API")


# ─── Factory Function ─────────────────────────────────────────────────────────

def get_llm_provider() -> LLMProvider:
    """Returns the configured LLMProvider based on environment variables."""
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider == "ollama":
        return OllamaProvider()
    elif provider == "openrouter":
        return OpenRouterProvider()
    elif provider == "gemini":
        return GeminiProvider()
    else:
        return MockProvider()
