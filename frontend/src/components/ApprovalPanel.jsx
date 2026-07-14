import { useState } from "react";

export default function ApprovalPanel({ ticket, onDecide, deciding }) {
  const [notes, setNotes] = useState("");
  const payload = ticket.interrupt_payload || {};

  return (
    <div className="panel gate-panel">
      <h3>Approval required</h3>
      <p style={{ fontSize: 13, color: "var(--paper)", marginTop: 0 }}>
        {payload.approval_reason || "This refund exceeds the auto-approval limit and needs sign-off."}
      </p>

      <div className="kv-grid" style={{ marginTop: 14 }}>
        <div className="kv-item">
          <div className="kv-label">Order</div>
          <div className="kv-value mono">{payload.order_id || ticket.order_id}</div>
        </div>
        <div className="kv-item">
          <div className="kv-label">Refund amount</div>
          <div className="kv-value mono">
            ${(payload.refund_amount ?? ticket.refund_amount ?? 0).toFixed(2)}
          </div>
        </div>
      </div>

      <textarea
        className="gate-notes"
        placeholder="Optional notes for this decision..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      <div className="gate-actions">
        <button
          className="btn-approve"
          disabled={deciding}
          onClick={() => onDecide("approved", notes)}
        >
          Approve refund
        </button>
        <button
          className="btn-reject"
          disabled={deciding}
          onClick={() => onDecide("rejected", notes)}
        >
          Reject
        </button>
      </div>
    </div>
  );
}
