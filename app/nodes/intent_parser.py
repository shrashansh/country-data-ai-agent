import logging
from typing import List

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.config import MODEL_NAME, SUPPORTED_COUNTRY_FIELDS
from app.models.state import AgentState

logger = logging.getLogger(__name__)

_SUPPORTED_FIELDS_STR = ", ".join(SUPPORTED_COUNTRY_FIELDS)

_SYSTEM_PROMPT = f"""You are an assistant that extracts structured information from user queries about countries.

Extract:
1. The country name the user is asking about.
2. The specific fields they want to know about.

Only include fields from this supported list: {_SUPPORTED_FIELDS_STR}.
If the user does not mention specific fields, return all supported fields.
"""


class QueryIntent(BaseModel):
    """Structured representation of the user's intent parsed from their query."""

    country: str = Field(description="The name of the country the user is asking about.")
    fields: List[str] = Field(
        description=(
            f"The country data fields requested by the user. "
            f"Must only contain values from: {_SUPPORTED_FIELDS_STR}."
        )
    )


def parse_query_node(state: AgentState) -> AgentState:
    """LangGraph node that extracts country name and requested fields."""

    if state.get("error"):
        return state

    user_query = state.get("user_query", "")

    if not user_query.strip():
        return {**state, "error": "Empty query provided."}

    logger.info("parse_query_node: parsing query %r", user_query)

    try:
        llm = ChatGroq(
            model=MODEL_NAME,
            temperature=0
        )
        structured_llm = llm.with_structured_output(QueryIntent)

        intent: QueryIntent = structured_llm.invoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ]
        )

        country = intent.country.strip()

        valid_fields = [f for f in intent.fields if f in SUPPORTED_COUNTRY_FIELDS]

        if not valid_fields:
            valid_fields = list(SUPPORTED_COUNTRY_FIELDS)

        logger.info(
            "parse_query_node: extracted country=%r fields=%r",
            country,
            valid_fields,
        )

        return {
            **state,
            "country": country,
            "fields": valid_fields,
            "error": None,
        }

    except Exception as exc:
        logger.error("parse_query_node: failed to parse query - %s", exc, exc_info=True)
        return {**state, "error": f"Failed to parse query: {exc}"}
