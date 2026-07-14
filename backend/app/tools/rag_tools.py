"""Tool available to the Technical agent: hybrid RAG search over support docs."""

from langchain_core.tools import tool

from app.rag.hybrid_retriever import hybrid_search


@tool
def search_support_docs(query: str) -> list[dict]:
    """
    Search the technical support documentation (password reset, API errors,
    billing FAQ, integrations) using hybrid dense+sparse retrieval and return
    the top matching chunks with their source file and RRF relevance score.
    """
    return hybrid_search(query, top_k=5)


RAG_TOOLS = [search_support_docs]
