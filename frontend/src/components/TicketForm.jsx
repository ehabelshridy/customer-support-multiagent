import { useState } from "react";

const PRESETS = [
  {
    label: "Password reset",
    customer_id: "CUST-DEMO1",
    message: "I never received the password reset email, what should I do?",
  },
  {
    label: "Invoice status",
    customer_id: "CUST-DEMO1",
    message: "Can you tell me the status of invoice INV-DEMO-OVERDUE?",
  },
  {
    label: "Small refund (auto)",
    customer_id: "CUST-DEMO1",
    message: "I'd like a refund for order ORD-DEMO-SMALL, it wasn't what I expected.",
  },
  {
    label: "Large refund (needs approval)",
    customer_id: "CUST-DEMO1",
    message: "Please refund order ORD-DEMO-LARGE, I want to cancel this purchase.",
  },
  {
    label: "Ineligible refund",
    customer_id: "CUST-DEMO1",
    message: "I want a refund for order ORD-DEMO-INELIGIBLE.",
  },
];

export default function TicketForm({ onSubmit, submitting }) {
  const [customerId, setCustomerId] = useState("CUST-DEMO1");
  const [message, setMessage] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    onSubmit(customerId, message);
    setMessage("");
  };

  return (
    <form className="ticket-form" onSubmit={handleSubmit}>
      <div>
        <label className="field-label" htmlFor="customer_id">
          Customer ID
        </label>
        <input
          id="customer_id"
          className="field-input"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          placeholder="CUST-1001"
        />
      </div>

      <div>
        <label className="field-label" htmlFor="message">
          Ticket message
        </label>
        <textarea
          id="message"
          className="field-textarea"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe the customer's issue..."
        />
      </div>

      <div className="presets">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            className="preset-chip"
            onClick={() => {
              setCustomerId(p.customer_id);
              setMessage(p.message);
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      <button className="btn-primary" type="submit" disabled={submitting || !message.trim()}>
        {submitting ? "Routing..." : "Submit ticket"}
      </button>
    </form>
  );
}
