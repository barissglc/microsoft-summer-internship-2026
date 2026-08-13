# AGENTS.md

RAG-based e-commerce support chatbot. FastAPI backend, React frontend,
Qdrant vector DB, Voyage AI embeddings, Gemini generation.

## Layout

- `backend/app/rag.py` — all retrieval + generation logic lives here
- `backend/app/main.py` — FastAPI routes (`/api/chat`, `/api/health`)
- `frontend/src/App.jsx` — single-file chat UI (React, Tailwind v4)
- `scripts/ingest.py` — one-time/resumable batch job that embeds the
  dataset into Qdrant (idempotent, checkpoint-based)
- `docs/adr/` — read before changing embedding, retrieval, or deployment
  behavior; each decision has a documented reason

## Conventions

- No code comments unless they explain a non-obvious *why* — see any
  existing file for the expected style.
- Env vars (`GEMINI_API_KEY`, `VOYAGE_API_KEY`, `QDRANT_URL`) are read via
  `os.environ` — never hardcode a key or fall back to a default secret.
- `backend/` and the root project have **separate** `pyproject.toml` /
  `uv.lock` — sync each independently with `uv sync`.
- The chatbot must reply in the same language the user asked in (see the
  system prompt in `rag.py`) — don't reintroduce a hardcoded output
  language.
- Both `ingest.py` (bulk) and `rag.py` (`embed_query`) must use the same
  Voyage model and `output_dimensionality`, or Qdrant similarity scores
  break silently.

## Testing a change

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8001
cd frontend && npm run dev
```

Hit `/api/chat` directly to check the RAG pipeline without the UI:

```bash
curl -X POST localhost:8001/api/chat -H 'Content-Type: application/json' \
  -d '{"message":"How can I track my order?","history":[]}'
```
