"""
Builds the retrieval indexes used by the Technical agent:
  - a Chroma vector store (dense retrieval) persisted to disk
  - a pickled BM25 index (sparse retrieval) persisted to disk

Run directly:
    python -m app.rag.build_index
"""

import os
import pickle
import glob

from langchain_text_splitters import MarkdownTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.config import SUPPORT_DOCS_DIR, CHROMA_PERSIST_DIR, get_embeddings

BM25_INDEX_PATH = os.path.join(os.path.dirname(__file__), "bm25_index.pkl")


def load_documents() -> list[Document]:
    splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=80)
    docs: list[Document] = []
    for path in sorted(glob.glob(os.path.join(SUPPORT_DOCS_DIR, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        source_name = os.path.basename(path)
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={"source": source_name, "chunk_index": i},
                )
            )
    return docs


def build_dense_index(docs: list[Document]) -> None:
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name="support_docs",
    )


def build_sparse_index(docs: list[Document]) -> None:
    tokenized = [d.page_content.lower().split() for d in docs]
    bm25 = BM25Okapi(tokenized)
    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "docs": docs}, f)


def main() -> None:
    docs = load_documents()
    print(f"Loaded {len(docs)} chunks from {SUPPORT_DOCS_DIR}")
    build_dense_index(docs)
    print(f"Dense (Chroma) index persisted to {CHROMA_PERSIST_DIR}")
    build_sparse_index(docs)
    print(f"Sparse (BM25) index persisted to {BM25_INDEX_PATH}")


if __name__ == "__main__":
    main()
