"""
Refund agent: extracts the order referenced in the ticket, checks refund
eligibility deterministically (via calculate_refund_eligibility), and decides
whether the request needs human approval based on a fixed dollar threshold.

The eligibility check runs BEFORE the approval gate on purpose: an order that
is not refundable (wrong status, already refunded, non-eligible product) is
rejected immediately instead of wasting a human reviewer's time.
"""

import re

from app.config import REFUND_AUTO_APPROVE_LIMIT
from app.state import SupportState
from app.tools.order_tools import calculate_refund_eligibility

ORDER_ID_PATTERN = re.compile(r"ORD-[A-Za-z0-9-]+", re.IGNORECASE)


def refund_agent(state: SupportState) -> dict:
    message = state["original_message"]
    match = ORDER_ID_PATTERN.search(message)

    if not match:
        return {
            "agent_response": (
                "I couldn't find an order number in your message. Please provide the "
                "order ID (format: ORD-XXXX) so I can process your refund request."
            ),
            "final_status": "escalated",
            "requires_approval": False,
        }

    order_id = match.group(0).upper()
    result = calculate_refund_eligibility.invoke(order_id)

    if not result["eligible"]:
        return {
            "order_id": order_id,
            "refund_eligible": False,
            "refund_ineligible_reason": result["reason"],
            "agent_response": f"Refund request for {order_id} cannot be processed: {result['reason']}.",
            "final_status": "resolved",
            "requires_approval": False,
        }

    amount = result["amount"]
    requires_approval = amount > REFUND_AUTO_APPROVE_LIMIT

    return {
        "order_id": order_id,
        "refund_eligible": True,
        "refund_amount": amount,
        "requires_approval": requires_approval,
        "approval_reason": (
            f"Refund amount ${amount:.2f} exceeds auto-approval limit of ${REFUND_AUTO_APPROVE_LIMIT:.2f}"
            if requires_approval
            else None
        ),
        "agent_response": (
            f"Order {order_id} is eligible for a ${amount:.2f} refund."
            + (" This requires manager approval before it is processed." if requires_approval else " Processing automatically.")
        ),
    }
