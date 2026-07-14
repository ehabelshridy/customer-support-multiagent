"""
FastAPI backend for the Customer Support Multi-Agent System.

Endpoints:
    POST /tickets                     submit a new ticket, runs the graph until
                                       it finishes OR pauses at human_approval
    GET  /tickets/{thread_id}         poll current status of a ticket
    POST /tickets/{thread_id}/approve resume a paused ticket with a human decision
    GET  /tickets                     list all tickets seen this process lifetime
    GET  /health                      liveness check
"""

import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Command

from app.graph import get_compiled_graph_with_sqlite_checkpointer

app = FastAPI(title="Customer Support Multi-Agent System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo project: tighten this for production deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph, _checkpointer_cm = get_compiled_graph_with_sqlite_checkpointer()

# In-memory index of thread_id -> lightweight ticket metadata, purely so the
# frontend can list tickets without re-querying every checkpoint. This is not
# the source of truth (the checkpointer is); it's just a UI convenience cache.
_ticket_index: dict[str, dict] = {}


class NewTicketRequest(BaseModel):
    customer_id: str
    message: str


class ApprovalRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str | None = None


def _snapshot_to_response(thread_id: str, snapshot) -> dict:
    state = snapshot.values
    is_interrupted = bool(snapshot.next)  # non-empty `next` means graph is paused

    interrupt_payload = None
    if is_interrupted and snapshot.tasks:
        for task in snapshot.tasks:
            if task.interrupts:
                interrupt_payload = task.interrupts[0].value
                break

    return {
        "thread_id": thread_id,
        "ticket_id": state.get("ticket_id"),
        "customer_id": state.get("customer_id"),
        "original_message": state.get("original_message"),
        "category": state.get("category"),
        "routing_confidence": state.get("routing_confidence"),
        "final_status": state.get("final_status"),
        "final_response": state.get("final_response"),
        "requires_approval": state.get("requires_approval", False),
        "awaiting_human": is_interrupted,
        "interrupt_payload": interrupt_payload,
        "order_id": state.get("order_id"),
        "refund_amount": state.get("refund_amount"),
        "retrieved_context": state.get("retrieved_context"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets")
def create_ticket(req: NewTicketRequest):
    thread_id = str(uuid.uuid4())
    ticket_id = f"TICKET-{thread_id[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "ticket_id": ticket_id,
        "customer_id": req.customer_id,
        "original_message": req.message,
        "retry_count": 0,
        "error_log": [],
        "requires_approval": False,
    }

    graph.invoke(initial_state, config=config)
    snapshot = graph.get_state(config)

    _ticket_index[thread_id] = {"ticket_id": ticket_id, "customer_id": req.customer_id}

    return _snapshot_to_response(thread_id, snapshot)


@app.get("/tickets")
def list_tickets():
    results = []
    for thread_id in _ticket_index:
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = graph.get_state(config)
        if snapshot.values:
            results.append(_snapshot_to_response(thread_id, snapshot))
    return results


@app.get("/tickets/{thread_id}")
def get_ticket(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _snapshot_to_response(thread_id, snapshot)


@app.post("/tickets/{thread_id}/approve")
def approve_ticket(thread_id: str, req: ApprovalRequest):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not snapshot.next:
        raise HTTPException(status_code=400, detail="Ticket is not awaiting approval")

    graph.invoke(
        Command(resume={"decision": req.decision, "notes": req.notes}),
        config=config,
    )
    result_snapshot = graph.get_state(config)
    return _snapshot_to_response(thread_id, result_snapshot)
