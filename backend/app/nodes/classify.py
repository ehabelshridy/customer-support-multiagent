"""
Supervisor node: classifies an incoming ticket into technical / billing /
refund, with a confidence score. Uses a JSON-constrained prompt + Pydantic
parser instead of provider-specific function calling so this works
identically whether LLM_PROVIDER is "huggingface" or "openai" (many
HuggingFace-hosted models do not support native tool calling).
"""

import json
import re

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_llm, ROUTING_CONFIDENCE_THRESHOLD
from app.state import SupportState


class ClassificationResult(BaseModel):
    category: str = Field(description="One of: technical, billing, refund, unclear")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="One sentence explaining the classification")


CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a support ticket router. Classify the customer's message into "
            "exactly one category: 'technical' (bugs, errors, integrations, how-to "
            "questions), 'billing' (invoices, payments, plan questions), 'refund' "
            "(explicit refund/money-back requests), or 'unclear' if the message is "
            "ambiguous or does not fit any category confidently.\n\n"
            "Respond with ONLY a JSON object, no markdown fences, no extra text, in "
            "exactly this shape:\n"
            '{{"category": "...", "confidence": 0.0, "reasoning": "..."}}',
        ),
        ("human", "{message}"),
    ]
)


def _extract_json(raw_text: str) -> dict:
    """Best-effort extraction of a JSON object from an LLM response, tolerant
    of stray markdown fences or leading/trailing text some models add."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {raw_text!r}")
    return json.loads(match.group(0))


def classify_ticket(state: SupportState) -> dict:
    llm = get_llm(temperature=0.0)
    chain = CLASSIFY_PROMPT | llm
    raw = chain.invoke({"message": state["original_message"]})
    raw_text = raw.content if hasattr(raw, "content") else str(raw)

    try:
        parsed = _extract_json(raw_text)
        result = ClassificationResult(**parsed)
    except Exception as e:
        # Fail safe into "unclear" rather than crashing the graph on a
        # malformed LLM response.
        return {
            "category": "unclear",
            "routing_confidence": 0.0,
            "routing_reasoning": f"Failed to parse classifier output: {e}",
            "error_log": state.get("error_log", []) + [f"classify_ticket parse error: {e}"],
        }

    category = result.category if result.confidence >= ROUTING_CONFIDENCE_THRESHOLD else "unclear"

    return {
        "category": category,
        "routing_confidence": result.confidence,
        "routing_reasoning": result.reasoning,
    }


def route_after_classification(state: SupportState) -> str:
    """Conditional edge function: decides the next node purely from state,
    no LLM call — deterministic and cheap."""
    category = state.get("category", "unclear")
    if category == "unclear":
        return "request_clarification"
    return category  # "technical" | "billing" | "refund"
