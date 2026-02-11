from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    session_id: str
    messages: List[Dict[str, Any]]
    user_input: str
    response: str
    next_node: str
