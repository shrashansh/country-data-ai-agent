import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from app.models.state import AgentState
from app.nodes.answer_synthesizer import answer_synthesizer
from app.nodes.country_tool_node import country_tool_node
from app.nodes.intent_parser import parse_query_node

logger = logging.getLogger(__name__)


def _route_on_error(state: AgentState) -> Literal["continue", "__end__"]:
    """Return '__end__' if an error is present in state, otherwise 'continue'."""
    if state.get("error"):
        logger.warning("Graph routing to END due to error: %s", state["error"])
        return "__end__"
    return "continue"


_agent_graph = None


def get_agent_graph():
    global _agent_graph

    if _agent_graph is not None:
        return _agent_graph

    builder = StateGraph(AgentState)

    builder.add_node("parse_query_node", parse_query_node)
    builder.add_node("country_tool_node", country_tool_node)
    builder.add_node("answer_synthesizer", answer_synthesizer)

    builder.set_entry_point("parse_query_node")

    builder.add_conditional_edges(
        "parse_query_node",
        _route_on_error,
        {"continue": "country_tool_node", "__end__": END},
    )

    builder.add_conditional_edges(
        "country_tool_node",
        _route_on_error,
        {"continue": "answer_synthesizer", "__end__": END},
    )

    builder.add_edge("answer_synthesizer", END)

    _agent_graph = builder.compile()
    logger.info("Agent graph compiled successfully")

    return _agent_graph