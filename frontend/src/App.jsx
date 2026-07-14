import { useEffect, useState, useCallback } from "react";
import { api } from "./api.js";
import TicketForm from "./components/TicketForm.jsx";
import ConversationView from "./components/ConversationView.jsx";
import StatusBadge from "./components/StatusBadge.jsx";

export default function App() {
  const [tickets, setTickets] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState(null);

  const refreshList = useCallback(async () => {
    try {
      const list = await api.listTickets();
      setTickets(list.reverse());
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    refreshList();
  }, [refreshList]);

  const selected = tickets.find((t) => t.thread_id === selectedId) || null;

  const handleSubmit = async (customerId, message) => {
    setSubmitting(true);
    setError(null);
    try {
      const ticket = await api.createTicket(customerId, message);
      setTickets((prev) => [ticket, ...prev]);
      setSelectedId(ticket.thread_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDecide = async (decision, notes) => {
    if (!selected) return;
    setDeciding(true);
    setError(null);
    try {
      const updated = await api.approveTicket(selected.thread_id, decision, notes);
      setTickets((prev) => prev.map((t) => (t.thread_id === updated.thread_id ? updated : t)));
    } catch (e) {
      setError(e.message);
    } finally {
      setDeciding(false);
    }
  };

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <div className="brand-dot" />
            <h1>Support Desk</h1>
          </div>
          <p>Supervisor-routed multi-agent console</p>
        </div>

        <TicketForm onSubmit={handleSubmit} submitting={submitting} />

        <div className="queue">
          {tickets.length === 0 && (
            <div className="queue-empty">No tickets yet — submit one above to see it routed.</div>
          )}
          {tickets.map((t) => (
            <div
              key={t.thread_id}
              className={`queue-item ${t.thread_id === selectedId ? "active" : ""}`}
              onClick={() => setSelectedId(t.thread_id)}
            >
              <div className="queue-item-top">
                <span className="queue-item-id mono">{t.ticket_id}</span>
                <StatusBadge ticket={t} />
              </div>
              <div className="queue-item-msg">{t.original_message}</div>
            </div>
          ))}
        </div>
      </aside>

      <main className="main">
        {error && <div className="error-banner">{error}</div>}

        {selected ? (
          <ConversationView ticket={selected} onDecide={handleDecide} deciding={deciding} />
        ) : (
          <div className="empty-state">
            <h2>Select or submit a ticket</h2>
            <p>The supervisor agent will classify it and route it to the right specialist.</p>
          </div>
        )}
      </main>
    </div>
  );
}
