import logging

from app.models.state import AgentState
from app.tools.rest_countries_tool import fetch_country_data
from app.utils.normalizer import normalize_country_data

logger = logging.getLogger(__name__)


def country_tool_node(state: AgentState) -> AgentState:
    """LangGraph node that fetches and normalises country data from the REST Countries API.

    Reads the ``country`` field from AgentState, calls the REST Countries API,
    normalises the raw response into a flat dictionary, and writes both back
    into the state.  Any pre-existing error in the state causes an immediate
    early return so that error handling can be centralised in the graph router.

    Args:
        state: The current AgentState.  Must contain a ``country`` value when
               no prior error is present.

    Returns:
        An updated AgentState with ``api_response`` and ``normalized_data``
        populated on success, or ``error`` populated on failure.
    """
    if state.get("error"):
        logger.warning(
            "country_tool_node: skipping execution — upstream error: %s", state["error"]
        )
        return state

    country = state.get("country")
    if not country:
        logger.error("country_tool_node: no country found in state")
        return {**state, "error": "No country name was extracted from the query."}

    logger.info("country_tool_node: fetching data for country %r", country)

    try:
        raw_data = fetch_country_data(country)
    except ValueError as exc:
        logger.warning("country_tool_node: country lookup failed — %s", exc)
        return {**state, "error": str(exc)}
    except Exception as exc:
        logger.error(
            "country_tool_node: unexpected error fetching %r — %s", country, exc, exc_info=True
        )
        return {**state, "error": f"Unexpected error while fetching country data: {exc}"}

    logger.info("country_tool_node: normalising response for %r", country)
    normalized = normalize_country_data(raw_data)
    if not normalized:
        logger.error("country_tool_node: normalization returned empty result")
        return {**state, "error": "Failed to process country data."}

    logger.info("country_tool_node: successfully processed data for %r", country)
    return {**state, "api_response": raw_data, "normalized_data": normalized, "error": None}
