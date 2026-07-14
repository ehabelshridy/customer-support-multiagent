export default function StatusBadge({ ticket }) {
  if (ticket.awaiting_human) {
    return <span className="badge badge-pending">Awaiting review</span>;
  }
  if (!ticket.final_status) {
    return <span className="badge badge-processing">Processing</span>;
  }
  if (ticket.final_status === "resolved") {
    return <span className="badge badge-resolved">Resolved</span>;
  }
  if (ticket.final_status === "escalated") {
    return <span className="badge badge-escalated">Escalated</span>;
  }
  return <span className="badge badge-processing">{ticket.final_status}</span>;
}
