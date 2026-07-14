# Customer Support Multi-Agent System

A supervisor-based multi-agent customer support system built with **LangGraph**,
**FastAPI**, and **React**. An incoming support ticket is classified by a
supervisor agent and routed to one of three specialist sub-agents (Technical,
Billing, Refund). Refunds above a configurable threshold pause the graph at a
**human-in-the-loop approval gate** (via LangGraph's `interrupt()`) until a
reviewer approves or rejects them from the frontend.

This project is a companion piece to [DocChat](https://github.com/ehabelshridy/agentic-rag)
(agentic RAG over FDA drug labels) — the Technical agent here reuses the same
hybrid retrieval pattern (ChromaDB dense + BM25 sparse + Reciprocal Rank Fusion).

---

## Architecture

```
                         START
                           │
                           ▼
                  ┌─────────────────┐
                  │  classify_ticket │   (LLM, structured JSON output)
                  └────────┬─────────┘
                           │
        confidence < 0.7 ──┴── confidence >= 0.7
              │                        │
              ▼                        ▼
  ┌──────────────────────┐   ┌─────────────────────────────┐
  │ request_clarification │   │        route_to_agent        │
  └──────────────────────┘   └───────────────┬───────────────┘
              │                               │
              ▼                ┌──────────────┼──────────────┐
             END                ▼              ▼              ▼
                     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                     │ technical_    │ │ billing_agent │ │ refund_agent │
                     │ agent (RAG)   │ │ (read-only DB)│ │ (order DB)   │
                     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                            │                │                │
                            │                │        needs_approval?
                            │                │           │        │
                            │                │          yes       no
                            │                │           │        │
                            │                │           ▼        │
                            │                │   ┌─────────────────┐
                            │                │   │  human_approval  │  <- interrupt()
                            │                │   └────────┬────────┘
                            │                │            ▼
                            │                │   ┌─────────────────┐
                            │                │   │  apply_decision  │
                            │                │   └────────┬────────┘
                            ▼                ▼             ▼
                     ┌──────────────────────────────────────────┐
                     │           compose_final_response           │
                     └──────────────────────────────────────────┘
                                        │
                                        ▼
                                       END
```

### Design decisions

- **Deterministic routing, not LLM-in-the-loop everywhere.** Only the
  classification step and the natural-language answer generation call an
  LLM. Eligibility checks, the approval threshold, and edge routing are plain
  Python — cheaper, faster, and fully auditable.
- **Structured output via JSON-constrained prompting**, not provider-specific
  function calling, so the same code works against HuggingFace Inference API
  models (which mostly don't support tool calling) or OpenAI.
- **Eligibility check runs before the approval gate.** An order that's
  already refunded, not eligible, or in the wrong status is rejected
  automatically — a human reviewer only ever sees requests that are
  legitimately borderline (amount over the threshold).
- **`interrupt()` + SqliteSaver checkpointer** for the human-in-the-loop gate.
  The graph genuinely pauses and persists to disk; approving a refund from
  the frontend hours later resumes execution from that exact node, not from
  the start.
- **Billing agent is strictly read-only** — it has no path to mutate data, so
  it never needs approval. Only the Refund agent's tools can create a
  pending state that requires sign-off.

### Tech stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph (`StateGraph`, `interrupt()`, `SqliteSaver`) |
| LLM access | HuggingFace Inference API (default) or OpenAI, swappable via `.env` |
| Technical agent retrieval | ChromaDB (dense) + BM25 (sparse) + Reciprocal Rank Fusion |
| Billing / Refund data | SQLite, seeded with Faker-generated mock data |
| API | FastAPI |
| Frontend | React (Vite) |
| Containerization | Docker + docker-compose |

---

## Project structure

```
customer-support-multiagent/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app + endpoints
│   │   ├── graph.py                # LangGraph StateGraph wiring
│   │   ├── state.py                # SupportState TypedDict
│   │   ├── config.py               # LLM provider factory, thresholds
│   │   ├── nodes/                  # classify, technical/billing/refund agents, approval
│   │   ├── tools/                  # DB + RAG tools per agent
│   │   ├── rag/                    # hybrid retriever (Chroma + BM25 + RRF)
│   │   └── db/                     # schema.sql, seed.py, database.py
│   ├── data/support_docs/          # markdown docs indexed by the Technical agent
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/             # TicketForm, ConversationView, ApprovalPanel, StatusBadge
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
└── README.md
```

---

## Running locally (without Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set HUGGINGFACEHUB_API_TOKEN=hf_xxx
# (or set LLM_PROVIDER=openai and OPENAI_API_KEY=sk-xxx)

python -m app.db.seed            # seeds SQLite with mock customers/orders/invoices
python -m app.rag.build_index    # builds the Chroma + BM25 indexes from support docs

uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env             # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:5173`.

---

## Running with Docker

```bash
cp backend/.env.example backend/.env
# edit backend/.env with your HUGGINGFACEHUB_API_TOKEN or OpenAI key

docker compose up --build
```

- Frontend: `http://localhost:4173`
- Backend: `http://localhost:8000`

The backend entrypoint seeds the database and builds the RAG indexes
automatically on first container start (this makes one embeddings API call),
then starts the API server.

---

## Demo walkthrough

The database is seeded with a fixed demo customer (`CUST-DEMO1`) and three
orders chosen to exercise every branch of the graph. The frontend's preset
chips fill these in automatically:

| Scenario | What it exercises |
|---|---|
| "I never received the password reset email" | Technical agent → hybrid RAG retrieval |
| "Status of invoice INV-DEMO-OVERDUE?" | Billing agent → read-only invoice lookup |
| Refund `ORD-DEMO-SMALL` ($45) | Refund agent → auto-approved, no human step |
| Refund `ORD-DEMO-LARGE` ($350) | Refund agent → **pauses at the approval gate** |
| Refund `ORD-DEMO-INELIGIBLE` | Refund agent → rejected automatically, no human step |

For the $350 refund, the ticket detail view shows an amber "Approval
required" panel with **Approve** / **Reject** buttons. Choosing either
resumes the paused LangGraph execution via `POST /tickets/{id}/approve`.

---

## API reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/tickets` | Submit a new ticket `{customer_id, message}` |
| `GET` | `/tickets` | List all tickets seen this process lifetime |
| `GET` | `/tickets/{thread_id}` | Get current status of a ticket |
| `POST` | `/tickets/{thread_id}/approve` | Resume a paused ticket: `{decision: "approved"\|"rejected", notes?}` |
| `GET` | `/health` | Liveness check |

---

## Configuration

All tunable values live in `backend/.env` (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `huggingface` | `huggingface` or `openai` |
| `HF_CHAT_MODEL` | `meta-llama/Llama-3.1-8B-Instruct` | HF Inference API chat model |
| `HF_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HF embedding model for RAG |
| `ROUTING_CONFIDENCE_THRESHOLD` | `0.7` | Below this, tickets go to `request_clarification` |
| `REFUND_AUTO_APPROVE_LIMIT` | `100` | Refunds above this dollar amount require human approval |
| `MAX_AGENT_RETRIES` | `2` | Retries before the Technical agent escalates on empty retrieval |

---

## Known limitations / next steps

- The in-memory `_ticket_index` in `main.py` is a UI convenience cache, not
  the source of truth (the SQLite checkpointer is) — it resets on server
  restart, so `/tickets` will show an empty list after a restart even though
  individual `GET /tickets/{thread_id}` calls still work if you have the ID.
  A production version would persist this index too.
- No authentication on the approval endpoint — anyone with a thread ID can
  approve/reject. Fine for a portfolio demo, not for production.
- Sub-agents extract IDs (order/invoice numbers) from the ticket message via
  regex rather than a full ReAct tool-calling loop, which keeps the system
  robust against LLMs that don't support function calling well. A production
  version could add a proper ReAct loop per agent as a follow-up.
