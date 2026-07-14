const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  createTicket: (customer_id, message) =>
    request("/tickets", { method: "POST", body: JSON.stringify({ customer_id, message }) }),

  listTickets: () => request("/tickets"),

  getTicket: (threadId) => request(`/tickets/${threadId}`),

  approveTicket: (threadId, decision, notes) =>
    request(`/tickets/${threadId}/approve`, {
      method: "POST",
      body: JSON.stringify({ decision, notes }),
    }),
};
