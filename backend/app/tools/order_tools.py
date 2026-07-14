"""
Tools available to the Refund agent. `calculate_refund_eligibility` performs
the pre-check logic (already-refunded, non-eligible product, wrong order
status) so obviously-invalid requests are rejected automatically instead of
consuming a human reviewer's time on the approval gate.
"""

from langchain_core.tools import tool

from app.db.database import fetch_one


@tool
def get_order_status(order_id: str) -> dict | None:
    """Return an order's full record (status, amount, refund_eligible flag) by order_id."""
    return fetch_one("SELECT * FROM orders WHERE order_id = ?", (order_id,))


@tool
def calculate_refund_eligibility(order_id: str) -> dict:
    """
    Determine whether an order is eligible for refund and, if so, the amount.

    Returns a dict with keys: eligible (bool), amount (float | None),
    reason (str, only present when not eligible).
    """
    order = fetch_one("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    if order is None:
        return {"eligible": False, "amount": None, "reason": f"Order {order_id} not found"}

    if order["status"] == "refunded":
        return {"eligible": False, "amount": None, "reason": "Order was already refunded"}

    if not order["refund_eligible"]:
        return {"eligible": False, "amount": None, "reason": "This product is not eligible for refund"}

    if order["status"] not in ("delivered", "shipped"):
        return {
            "eligible": False,
            "amount": None,
            "reason": f"Order status '{order['status']}' is not refundable",
        }

    return {"eligible": True, "amount": order["amount"], "reason": None}


ORDER_TOOLS = [get_order_status, calculate_refund_eligibility]
