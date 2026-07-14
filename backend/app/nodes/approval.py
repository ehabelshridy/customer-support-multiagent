"""
Human-in-the-loop node. Uses LangGraph's `interrupt()` to pause graph
execution and persist state via the checkpointer. The graph resumes exactly
at this point (not from the start) once a human submits a decision through
POST /approval/{thread_id}.
"""

from langgraph.types import interrupt

from app.state import SupportState


def needs_approval(state: SupportState) -> bool:
    """Conditional edge predicate: deterministic, no LLM call."""
    return bool(state.get("requires_approval"))


def human_approval(state: SupportState) -> dict:
    """
    Pauses the graph and surfaces everything a reviewer needs to decide:
    the order/refund details and the reason approval was triggered.

    `interrupt()` raises a special exception under the hood that LangGraph's
    checkpointer catches to persist state; when the graph is resumed with a
    Command(resume=...), this function's return value becomes that resume
    value.
    """
    decision_payload = interrupt(
        {
            "ticket_id": state.get("ticket_id"),
            "order_id": state.get("order_id"),
            "refund_amount": state.get("refund_amount"),
            "approval_reason": state.get("approval_reason"),
            "original_message": state.get("original_message"),
        }
    )
    # decision_payload is provided by the human reviewer on resume, e.g.:
    # {"decision": "approved" | "rejected", "notes": "..."}
    return {
        "human_decision": decision_payload.get("decision"),
        "human_notes": decision_payload.get("notes"),
    }


def apply_decision(state: SupportState) -> dict:
    decision = state.get("human_decision")
    if decision == "approved":
        return {
            "final_status": "resolved",
            "agent_response": (
                f"Refund of ${state.get('refund_amount', 0):.2f} for order "
                f"{state.get('order_id')} was approved and processed."
            ),
        }
    elif decision == "rejected":
        notes = state.get("human_notes") or "No reason provided."
        return {
            "final_status": "resolved",
            "agent_response": (
                f"Refund request for order {state.get('order_id')} was reviewed and "
                f"declined. Reason: {notes}"
            ),
        }
    else:
        return {
            "final_status": "escalated",
            "agent_response": "Refund request is still pending human review.",
        }
