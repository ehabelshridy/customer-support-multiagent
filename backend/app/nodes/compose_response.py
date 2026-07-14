"""Terminal nodes: final response composition and clarification requests."""

from app.state import SupportState


def request_clarification(state: SupportState) -> dict:
    return {
        "final_status": "escalated",
        "final_response": (
            "I'm not confident I understood your request "
            f"(routing confidence: {state.get('routing_confidence', 0):.2f}). "
            "Could you clarify whether this is a technical issue, a billing "
            "question, or a refund request?"
        ),
    }


def compose_final_response(state: SupportState) -> dict:
    if state.get("final_response"):
        return {}

    status = state.get("final_status") or ("escalated" if state.get("requires_approval") else "resolved")
    response = state.get("agent_response") or "Your request has been received and is being processed."

    return {
        "final_status": status,
        "final_response": response,
    }
