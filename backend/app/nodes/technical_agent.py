"""
Technical agent: retrieves relevant support-doc chunks via hybrid RAG
(reused from the DocChat retrieval pipeline: Chroma dense + BM25 sparse +
RRF fusion) and generates a grounded answer. If retrieval returns nothing
useful, it escalates instead of letting the LLM hallucinate an answer.
"""

from langchain_core.prompts import ChatPromptTemplate

from app.config import get_llm, MAX_AGENT_RETRIES
from app.state import SupportState
from app.tools.rag_tools import search_support_docs

MIN_RELEVANCE_SCORE = 0.01  # RRF scores below this are treated as "no real match"

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a technical support agent. Answer the customer's question using "
            "ONLY the provided documentation context. Be concise and concrete. If the "
            "context does not fully answer the question, say what you can and note "
            "that the rest requires human follow-up. Do not invent steps that are not "
            "in the context.\n\nContext:\n{context}",
        ),
        ("human", "{message}"),
    ]
)


def technical_agent(state: SupportState) -> dict:
    query = state["original_message"]
    chunks = search_support_docs.invoke(query)

    useful_chunks = [c for c in chunks if c["rrf_score"] >= MIN_RELEVANCE_SCORE]

    if not useful_chunks:
        retry_count = state.get("retry_count", 0) + 1
        if retry_count > MAX_AGENT_RETRIES:
            return {
                "retrieved_context": chunks,
                "agent_response": None,
                "retry_count": retry_count,
                "final_status": "escalated",
                "error_log": state.get("error_log", []) + ["technical_agent: no relevant docs found after retries"],
            }
        return {
            "retrieved_context": chunks,
            "retry_count": retry_count,
        }

    context_text = "\n\n".join(f"[{c['source']}] {c['content']}" for c in useful_chunks)
    llm = get_llm(temperature=0.2)
    chain = ANSWER_PROMPT | llm
    response = chain.invoke({"context": context_text, "message": query})
    answer = response.content if hasattr(response, "content") else str(response)

    return {
        "retrieved_context": useful_chunks,
        "agent_response": answer,
        "requires_approval": False,
    }
