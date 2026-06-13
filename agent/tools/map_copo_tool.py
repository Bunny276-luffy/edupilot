"""
Tool: map_copo
Maps a question to Course Outcomes and Program Outcomes.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from services.blooms_classifier import assign_co_from_bloom


async def map_copo_tool(inputs: dict) -> dict:
    """
    Inputs:
      question (str): The exam question.
      blooms_level (str): Optional pre-classified Bloom's level.
    Outputs:
      dict: {co_mapping, po_mapping}
    """
    blooms_level = inputs.get("blooms_level", "Understand")
    co_mapping = assign_co_from_bloom(blooms_level)

    # Simple heuristic PO mapping
    po_mapping_rules = {
        "CO1": ["PO1"],
        "CO2": ["PO1", "PO2"],
        "CO3": ["PO2", "PO4"],
        "CO4": ["PO3", "PO5"],
        "CO5": ["PO4", "PO5"],
    }
    po_mapping = []
    for co in co_mapping:
        po_mapping.extend(po_mapping_rules.get(co, ["PO1"]))
    po_mapping = list(dict.fromkeys(po_mapping))  # deduplicate while preserving order

    return {"co_mapping": co_mapping, "po_mapping": po_mapping}
