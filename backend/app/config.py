"""
Central configuration for the Customer Support Multi-Agent System.

LLM_PROVIDER controls which backend is used for all agent LLM calls:
  - "huggingface" (default): uses HuggingFace Inference API, no local model download.
  - "openai": uses the OpenAI Chat Completions API.

Both providers are wrapped behind a single get_llm() factory so that
every node in the graph is provider-agnostic.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# General settings
# ---------------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface").lower()

# HuggingFace settings
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
HF_CHAT_MODEL = os.getenv("HF_CHAT_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# OpenAI settings (optional alternative provider)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# Routing / business thresholds
ROUTING_CONFIDENCE_THRESHOLD = float(os.getenv("ROUTING_CONFIDENCE_THRESHOLD", "0.7"))
REFUND_AUTO_APPROVE_LIMIT = float(os.getenv("REFUND_AUTO_APPROVE_LIMIT", "100"))
MAX_AGENT_RETRIES = int(os.getenv("MAX_AGENT_RETRIES", "2"))

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "app", "db", "support_system.db"))
SCHEMA_PATH = os.path.join(BASE_DIR, "app", "db", "schema.sql")
SUPPORT_DOCS_DIR = os.path.join(BASE_DIR, "data", "support_docs")
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "app", "rag", "chroma_store")

# Checkpointer (for LangGraph interrupt / human-in-the-loop persistence)
CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", os.path.join(BASE_DIR, "app", "db", "checkpoints.db"))


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.0):
    """
    Factory that returns a chat model instance based on LLM_PROVIDER.
    Cached per temperature value to avoid re-instantiating clients.

    Note: lru_cache on a function with a float arg works fine here since
    only a handful of fixed temperature values are used across the codebase.
    """
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        if not OPENAI_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set in the environment."
            )
        return ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=temperature, api_key=OPENAI_API_KEY)

    # Default: HuggingFace Inference API
    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

    if not HF_TOKEN:
        raise RuntimeError(
            "LLM_PROVIDER is 'huggingface' but HUGGINGFACEHUB_API_TOKEN is not set in the environment."
        )
    endpoint = HuggingFaceEndpoint(
        repo_id=HF_CHAT_MODEL,
        huggingfacehub_api_token=HF_TOKEN,
        temperature=max(temperature, 0.01),  # HF endpoint rejects temperature=0
        max_new_tokens=1024,
    )
    return ChatHuggingFace(llm=endpoint)


@lru_cache(maxsize=1)
def get_embeddings():
    """Factory for the embedding model used by the dense (Chroma) retriever."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(api_key=OPENAI_API_KEY)

    from langchain_huggingface import HuggingFaceEndpointEmbeddings

    return HuggingFaceEndpointEmbeddings(
        model=HF_EMBEDDING_MODEL,
        huggingfacehub_api_token=HF_TOKEN,
    )
