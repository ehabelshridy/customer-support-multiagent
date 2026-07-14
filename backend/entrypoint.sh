#!/bin/sh
set -e

if [ ! -f "app/db/support_system.db" ]; then
  echo "[entrypoint] Seeding database..."
  python -m app.db.seed
fi

if [ ! -f "app/rag/bm25_index.pkl" ]; then
  echo "[entrypoint] Building RAG indexes (this calls the embeddings API once)..."
  python -m app.rag.build_index
fi

echo "[entrypoint] Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
