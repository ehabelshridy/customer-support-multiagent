"""
Billing agent: looks up the customer's invoices (read-only, no writes) and
explains their billing status in plain language. Never needs human approval
since it cannot mutate any data.
"""

import re

from langchain_core.prompts import ChatPromptTemplate

from app.config import get_llm
from app.state import SupportState
from app.tools.billing_tools import get_customer_invoices, get_customer_profile

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a billing support agent. Using the customer's profile and invoice "
            "records below, answer their question clearly. Mention specific invoice "
            "IDs, amounts, and statuses where relevant. If there is no billing data "
            "for this customer, say so plainly instead of guessing.\n\n"
            "Customer profile:\n{profile}\n\nInvoices:\n{invoices}",
        ),
        ("human", "{message}"),
    ]
)

INVOICE_ID_PATTERN = re.compile(r"INV-\d+", re.IGNORECASE)


def billing_agent(state: SupportState) -> dict:
    customer_id = state["customer_id"]
    message = state["original_message"]

    profile = get_customer_profile.invoke(customer_id)
    invoices = get_customer_invoices.invoke(customer_id)

    invoice_match = INVOICE_ID_PATTERN.search(message)
    invoice_id = invoice_match.group(0).upper() if invoice_match else None

    llm = get_llm(temperature=0.2)
    chain = ANSWER_PROMPT | llm
    response = chain.invoke(
        {
            "profile": profile or "No profile found",
            "invoices": invoices or "No invoices found",
            "message": message,
        }
    )
    answer = response.content if hasattr(response, "content") else str(response)

    return {
        "agent_response": answer,
        "invoice_id": invoice_id,
        "requires_approval": False,
    }
