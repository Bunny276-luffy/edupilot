"""
Tool: socratic_tutor
Generates a Socratic tutoring response for a student query.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from routes.student import socratic_response


async def socratic_tutor_tool(inputs: dict) -> dict:
    """
    Inputs:
      topic (str): The subject/topic being studied.
      message (str): The student's latest message.
      history (list): Prior conversation [{role, content}].
      exchange_count (int): Number of prior exchanges.
    Outputs:
      dict: {reply, understanding_level}
    """
    topic = inputs.get("topic", "")
    message = inputs.get("message", "")
    history = inputs.get("history", [])
    exchange_count = int(inputs.get("exchange_count", 0))

    if not message:
        return {"error": "message field is required"}

    full_history = history + [{"role": "user", "content": message}]
    result = await socratic_response(
        topic=topic,
        conversation_history=full_history,
        exchange_count=exchange_count,
    )
    return result
