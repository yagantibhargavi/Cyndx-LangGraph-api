from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import planner_node, tool_node, responder_node


def route_from_planner(state: AgentState) -> str:
    """
    Decide where to go after planner.
    Prefer planner decision if you store it in state['next_node'].
    Fallback: keyword-based routing.
    """
    decision = (state.get("next_node") or "").lower()
    if decision in {"tool", "tools", "tool_node"}:
        return "tool"

    # fallback keyword routing (works even if planner_node doesn't set next_node)
    text = (state.get("user_input") or _last_user_text_fallback(state)).lower()
    if "weather" in text:
        return "tool"

    return "responder"


def _last_user_text_fallback(state: AgentState) -> str:
    msgs = state.get("messages", []) or []
    for m in reversed(msgs):
        if m.get("role") == "user" and m.get("content"):
            return str(m["content"])
    return ""


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("planner", planner_node)
    g.add_node("tool", tool_node)
    g.add_node("responder", responder_node)

    g.set_entry_point("planner")

    # ✅ conditional routing
    g.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "tool": "tool",
            "responder": "responder",
        },
    )

    # ✅ tool should be final (don’t call LLM again after tool)
    g.add_edge("tool", END)
    g.add_edge("responder", END)

    return g.compile()


agent_graph = build_graph()
