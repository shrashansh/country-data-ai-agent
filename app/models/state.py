from typing import Any, Optional, TypedDict, List, Dict


class AgentState(TypedDict):
    """
    Shared state object passed between LangGraph nodes.

    Each node reads from and updates this state as the request
    moves through the agent workflow.
    """

    user_query: str
    country: Optional[str]
    fields: List[str]

    api_response: Optional[Dict[str, Any]]
    normalized_data: Optional[Dict[str, Any]]

    result: Optional[Dict[str, Any]]
    error: Optional[str]