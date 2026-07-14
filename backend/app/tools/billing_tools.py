"""
Tools available to the Billing agent. All tools are strictly read-only —
the Billing agent never writes to the database, which keeps it out of scope
for the human-in-the-loop approval gate (only refunds mutate state).
"""

from langchain_core.tools import tool

from app.db.database import fetch_one, fetch_all


@tool
def get_customer_invoices(customer_id: str) -> list[dict]:
    """Return all invoices for a given customer_id, most recent first."""
    return fetch_all(
        "SELECT * FROM invoices WHERE customer_id = ? ORDER BY billing_date DESC",
        (customer_id,),
    )


@tool
def get_invoice_by_id(invoice_id: str) -> dict | None:
    """Return a single invoice by its invoice_id, or None if it doesn't exist."""
    return fetch_one("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))


@tool
def get_customer_profile(customer_id: str) -> dict | None:
    """Return the customer's plan, signup date, and account status."""
    return fetch_one("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))


BILLING_TOOLS = [get_customer_invoices, get_invoice_by_id, get_customer_profile]
