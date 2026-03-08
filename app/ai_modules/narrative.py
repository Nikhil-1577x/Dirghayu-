"""
narrative.py – Stub for AI clinical narrative generation.

In production, integrate with an LLM (e.g., Gemini, GPT-4, Claude) to generate
a natural language clinical summary from structured biomarker data.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_summary(biomarker_dict: dict[str, float]) -> str:
    """
    Generate a natural language clinical summary from biomarkers.

    Args:
        biomarker_dict: e.g. {"blood_glucose": 97.5, "blood_pressure": 120.0}

    Returns:
        str: Human-readable clinical narrative.
    """
    logger.debug("generate_summary called with %d biomarkers", len(biomarker_dict))

    if not biomarker_dict:
        return "No biomarker data is currently available for this patient."

    # ── STUB rule-based narrative ───────────────────────────────────────────
    # Replace with:
    #   from openai import OpenAI
    #   client = OpenAI()
    #   response = client.chat.completions.create(
    #       model="gpt-4o",
    #       messages=[{"role": "user", "content": f"Summarise these biomarkers: {biomarker_dict}"}]
    #   )
    #   return response.choices[0].message.content

    lines = []
    for marker, value in biomarker_dict.items():
        marker_label = marker.replace("_", " ").title()
        flag = ""
        if "glucose" in marker and value > 126:
            flag = " ⚠️ Elevated"
        elif "pressure" in marker and value > 140:
            flag = " ⚠️ Elevated"
        elif "oxygen" in marker and value < 95:
            flag = " ⚠️ Below normal"
        lines.append(f"  • {marker_label}: {value}{flag}")

    body = "\n".join(lines)
    return (
        f"Clinical Biomarker Summary:\n{body}\n\n"
        f"The patient's biomarker profile has been reviewed. "
        f"{('Elevated readings detected – clinician follow-up recommended.' if '⚠️' in body else 'All readings appear within acceptable ranges.')}"
    )
