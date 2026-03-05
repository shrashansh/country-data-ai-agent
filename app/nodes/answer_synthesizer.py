import json
import logging

from langchain_groq import ChatGroq

from app.config import MODEL_NAME
from app.models.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """
You are a helpful assistant that answers questions about countries.

You will receive:
1. A country name
2. A JSON object containing country data

Write a clear natural language answer using only the information provided.
Do not add facts that are not present in the JSON data.
"""


def answer_synthesizer(state: AgentState) -> AgentState:
    """LangGraph node that generates a natural language answer from normalised country data.

    Reads ``normalized_data`` and ``fields`` from AgentState, extracts only the
    fields the user asked for, sends them to a Groq-hosted LLM to produce a
    human-readable answer, and stores a structured result object back in the
    state.

    Args:
        state: The current AgentState.  Must contain ``normalized_data`` and
               ``fields`` when no prior error is present.

    Returns:
        An updated AgentState with ``result`` populated on success, or
        ``error`` populated on failure.  The result dict has the shape::

            {
                "country": str,
                "fields": list[str],
                "data":   dict,
                "answer": str,
            }
    """
    if state.get("error"):
        logger.warning(
            "answer_synthesizer: skipping execution — upstream error: %s", state["error"]
        )
        return state

    normalized_data = state.get("normalized_data")
    if not normalized_data:
        logger.error("answer_synthesizer: normalized_data is missing from state")
        return {**state, "error": "No normalised country data available to synthesise an answer."}

    country = state.get("country", "Unknown")
    requested_fields = state.get("fields") or []

    filtered_data = {
        field: normalized_data[field]
        for field in requested_fields
        if field in normalized_data
        }

    if not filtered_data:
        filtered_data = dict(normalized_data)

    logger.info(
        "answer_synthesizer: synthesising answer for %r with fields %r", country, requested_fields
    )

    user_message = (
        f"Country: {country}\n"
        f"Data: {json.dumps(filtered_data, ensure_ascii=False, indent=2)}"
    )

    try:
        llm = ChatGroq(model=MODEL_NAME, temperature=0)
        response = llm.invoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )
        answer: str = response.content.strip()
    except Exception as exc:
        logger.error("answer_synthesizer: LLM call failed — %s", exc, exc_info=True)
        return {**state, "error": f"Failed to generate answer: {exc}"}

    result = {
        "country": country,
        "fields": requested_fields,
        "data": filtered_data,
        "answer": answer,
    }

    logger.info("answer_synthesizer: answer generated successfully for %r", country)
    return {**state, "result": result, "error": None}
