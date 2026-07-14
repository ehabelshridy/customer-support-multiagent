"""
Shared state schema passed between every node in the LangGraph StateGraph.

This is intentionally a flat TypedDict (rather than nested objects) because
LangGraph applies reducers per-key, and flat structures make partial updates
from each node simple and predictable.
"""

from typing import TypedDict, Optional, Literal, List, Dict, Any


class SupportState(TypedDict, total=False):
    # ---- Input -------------------------------------------------------
    ticket_id: str
    customer_id: str
    original_message: str

    # ---- Routing -------------------------------------------------------
    category: Optional[Literal["technical", "billing", "refund", "unclear"]]
    routing_confidence: float
    routing_reasoning: str

    # ---- Sub-agent processing -------------------------------------------------------
    agent_response: Optional[str]
    retrieved_context: Optional[List[Dict[str, Any]]]  # RAG chunks (technical agent)
    order_id: Optional[str]
    invoice_id: Optional[str]
    refund_amount: Optional[float]
    refund_eligible: Optional[bool]
    refund_ineligible_reason: Optional[str]

    # ---- Human-in-the-loop -------------------------------------------------------
    requires_approval: bool
    approval_reason: Optional[str]
    human_decision: Optional[Literal["approved", "rejected", "modified"]]
    human_notes: Optional[str]

    # ---- Control flow -------------------------------------------------------
    retry_count: int
    error_log: List[str]
    final_status: Optional[Literal["resolved", "escalated", "pending_human"]]
    final_response: Optional[str]
