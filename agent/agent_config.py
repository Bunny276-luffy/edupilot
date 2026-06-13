"""
Agent configuration — defines Gemini-based agent with tool bindings.
This module sets up the tool registry and a convenience function for
dispatching agent calls.
"""
import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

# Import agent tools
from tools.classify_bloom_tool import classify_bloom_tool
from tools.map_copo_tool import map_copo_tool
from tools.search_papers_tool import search_papers_tool
from tools.socratic_tutor_tool import socratic_tutor_tool

# ── Tool Registry ─────────────────────────────────────────────────────────────
TOOLS = {
    "classify_bloom": classify_bloom_tool,
    "map_copo": map_copo_tool,
    "search_papers": search_papers_tool,
    "socratic_tutor": socratic_tutor_tool,
}

AGENT_SYSTEM_PROMPT = """You are EduPilot, an AI academic agent for Indian engineering colleges.
You assist faculty with NAAC/NBA accreditation (Bloom's taxonomy, CO-PO mapping, report generation)
and students with Socratic tutoring on their subjects.

Available tools:
- classify_bloom: Classify exam questions by Bloom's taxonomy level
- map_copo: Map questions to Course Outcomes and Program Outcomes
- search_papers: Search past university question papers
- socratic_tutor: Guide a student using the Socratic method

Always respond in clear, professional language. For faculty tasks, use academic terminology.
For student interactions, be encouraging and guiding — never give direct answers."""


async def dispatch_tool(tool_name: str, inputs: dict[str, Any]) -> Any:
    """
    Dispatch a tool call by name with given inputs.
    Returns the tool's output.
    """
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}. Available: {list(TOOLS.keys())}")
    tool_fn = TOOLS[tool_name]
    return await tool_fn(inputs)
