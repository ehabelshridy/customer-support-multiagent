import StatusBadge from "./StatusBadge.jsx";
import ApprovalPanel from "./ApprovalPanel.jsx";

const AGENT_LABELS = {
  technical: "Technical agent",
  billing: "Billing agent",
  refund: "Refund agent",
  unclear: "Clarification",
};

function RoutingRail({ ticket }) {
  const hasCategory = Boolean(ticket.category && ticket.category !== "unclear");
  const isGated = Boolean(ticket.requires_approval || ticket.awaiting_human);
  const isDone = Boolean(ticket.final_status);

  const stages = [
    { key: "supervisor", label: "Supervisor" },
    { key: "agent", label: hasCategory ? AGENT_LABELS[ticket.category] : "Agent" },
  ];
  if (isGated) stages.push({ key: "gate", label: "Approval gate" });
  stages.push({ key: "done", label: ticket.final_status === "escalated" ? "Escalated" : "Resolved" });

  const stageState = (key) => {
    if (key === "supervisor") return "done";
    if (key === "agent") return hasCategory ? (isGated || isDone ? "done" : "active") : "active";
    if (key === "gate") return ticket.awaiting_human ? "waiting" : "done";
    if (key === "done") return isDone ? "done" : "";
    return "";
  };

  return (
    <div className="rail">
      <div className="rail-line" />
      {stages.map((s) => (
        <div key={s.key} className={`rail-stage ${stageState(s.key)}`}>
          <div className="rail-node">{stageState(s.key) === "done" ? "✓" : ""}</div>
          <div className="rail-label">{s.label}</div>
        </div>
      ))}
    </div>
  );
}

export default function ConversationView({ ticket, onDecide, deciding }) {
  return (
    <div>
      <div className="detail-header">
        <div>
          <h2 className="mono">{ticket.ticket_id}</h2>
          <div className="detail-meta">
            <span className="mono">{ticket.customer_id}</span>
            {ticket.category && <> · {AGENT_LABELS[ticket.category] || ticket.category}</>}
            {typeof ticket.routing_confidence === "number" && (
              <> · confidence {ticket.routing_confidence.toFixed(2)}</>
            )}
          </div>
        </div>
        <StatusBadge ticket={ticket} />
      </div>

      <RoutingRail ticket={ticket} />

      <div className="panel">
        <h3>Customer message</h3>
        <div className="panel-response">{ticket.original_message}</div>
      </div>

      {ticket.awaiting_human && (
        <ApprovalPanel ticket={ticket} onDecide={onDecide} deciding={deciding} />
      )}

      {ticket.final_response && (
        <div className="panel">
          <h3>Response</h3>
          <div className="panel-response">{ticket.final_response}</div>
        </div>
      )}

      {(ticket.order_id || ticket.refund_amount != null) && (
        <div className="panel">
          <h3>Refund details</h3>
          <div className="kv-grid">
            {ticket.order_id && (
              <div className="kv-item">
                <div className="kv-label">Order ID</div>
                <div className="kv-value mono">{ticket.order_id}</div>
              </div>
            )}
            {ticket.refund_amount != null && (
              <div className="kv-item">
                <div className="kv-label">Amount</div>
                <div className="kv-value mono">${ticket.refund_amount.toFixed(2)}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {ticket.retrieved_context && ticket.retrieved_context.length > 0 && (
        <div className="panel">
          <h3>Retrieved context (hybrid RAG)</h3>
          {ticket.retrieved_context.map((chunk, i) => (
            <div key={i} className="context-chunk">
              <div className="context-chunk-source">
                {chunk.source} · rrf {chunk.rrf_score}
              </div>
              <div className="context-chunk-text">{chunk.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
