"""
Builds the LangGraph StateGraph for the Customer Support Multi-Agent System.

Flow:
    START -> classify_ticket -> (route)
        -> request_clarification -> END
        -> technical_agent -> compose_final_response -> END
        -> billing_agent   -> compose_final_response -> END
        -> refund_agent    -> (needs_approval?)
                -> human_approval -> apply_decision -> compose_final_response -> END
                -> compose_final_response -> END

A SqliteSaver checkpointer persists state at every step, which is what makes
`interrupt()` in human_approval actually pause-and-resume across separate
HTTP requests instead of just within a single process call stack.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from app.state import SupportState
from app.config import CHECKPOINT_DB_PATH
from app.nodes.classify import classify_ticket, route_after_classification
from app.nodes.technical_agent import technical_agent
from app.nodes.billing_agent import billing_agent
from app.nodes.refund_agent import refund_agent
from app.nodes.approval import needs_approval, human_approval, apply_decision
from app.nodes.compose_response import request_clarification, compose_final_response


def build_graph(checkpointer=None):
    graph = StateGraph(SupportState)

    graph.add_node("classify_ticket", classify_ticket)
    graph.add_node("request_clarification", request_clarification)
    graph.add_node("technical_agent", technical_agent)
    graph.add_node("billing_agent", billing_agent)
    graph.add_node("refund_agent", refund_agent)
    graph.add_node("human_approval", human_approval)
    graph.add_node("apply_decision", apply_decision)
    graph.add_node("compose_final_response", compose_final_response)

    graph.add_edge(START, "classify_ticket")

    graph.add_conditional_edges(
        "classify_ticket",
        route_after_classification,
        {
            "request_clarification": "request_clarification",
            "technical": "technical_agent",
            "billing": "billing_agent",
            "refund": "refund_agent",
        },
    )

    # Technical agent may loop back to itself (via retry_count) if retrieval
    # comes back empty; route_after_classification already sent it here once,
    # so on subsequent partial-state updates the caller re-invokes the graph.
    graph.add_conditional_edges(
        "technical_agent",
        lambda state: "end" if (state.get("agent_response") or state.get("final_status") == "escalated") else "retry",
        {"end": "compose_final_response", "retry": "technical_agent"},
    )

    graph.add_edge("billing_agent", "compose_final_response")

    graph.add_conditional_edges(
        "refund_agent",
        lambda state: "human_approval" if needs_approval(state) else "compose_final_response",
        {"human_approval": "human_approval", "compose_final_response": "compose_final_response"},
    )

    graph.add_edge("human_approval", "apply_decision")
    graph.add_edge("apply_decision", "compose_final_response")
    graph.add_edge("request_clarification", END)
    graph.add_edge("compose_final_response", END)

    return graph.compile(checkpointer=checkpointer)


def get_compiled_graph_with_sqlite_checkpointer():
    """
    Convenience factory used by main.py. SqliteSaver.from_conn_string
    returns a context manager in recent langgraph versions; for a long-lived
    FastAPI app we open it once and keep it alive for the process lifetime.
    """
    cm = SqliteSaver.from_conn_string(CHECKPOINT_DB_PATH)
    checkpointer = cm.__enter__()
    graph = build_graph(checkpointer=checkpointer)
    return graph, cm
