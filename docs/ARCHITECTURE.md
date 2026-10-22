# Architecture

atlas_ai_platform is a FastAPI service that stores document chunks in SQLite, generates replies through a pluggable LLM layer, and answers questions by retrieving similar chunks.

## Layout

```
app/
  main.py                 FastAPI app, DB init, background cleanup
  api/                    HTTP routes
  core/                   settings, SQLAlchemy models, feature flags
  providers/              mock / OpenAI / Anthropic adapters and fallback
  services/               cache, rate limit, chunking, embeddings, RAG, cleanup
tests/                    two smoke tests (health + mock chat)
```

## Request flow

```
Client
  |-- GET  /health        -> api.health.health
  |-- POST /chat          -> rate limit -> optional prompt log -> cache -> provider
  |-- POST /documents     -> chunk -> embed -> SQLite
  |-- POST /ask           -> embed query -> cosine retrieve -> provider
  |-- GET  /internal/stats
  |-- POST /internal/cache/flush
```

`app/main.py` registers the public routers and the `/internal` router on startup. Lifespan calls `init_db()` then starts `_chunk_cleanup_loop()`.

Chat (`app/api/chat.py::chat`) keys the limiter on `X-Client-Id` (or `anonymous`), optionally writes the raw message via `app/services/prompt_log.py::log_prompt`, looks up `app/services/cache.py::response_cache`, then calls `app/providers/factory.py::get_llm_provider()`.

Document ingest (`app/api/documents.py::create_document`) delegates to `app/services/rag.py::ingest_document`, which splits text in `chunk_text`, embeds each piece, and persists `Document` / `Chunk` rows.

Ask (`app/api/ask.py::ask`) calls `answer_with_context`, which scores all stored embeddings with cosine similarity and sends the top-k snippets to the same LLM factory.

## Data model

SQLite (default `sqlite:///./atlas.db`) via SQLAlchemy 2.0.

- `documents`: `id`, `source`, `created_at`
- `chunks`: `id`, `document_id` (FK), `text`, `embedding` (JSON float array), `created_at`

Embeddings are local SHA-256 hash vectors (`app/services/embeddings.py::embed_text`), not a remote embedding API. That keeps RAG offline and deterministic.

## Provider layer

`LLM_PROVIDER` selects mock (default), openai, or anthropic. Non-mock primaries are wrapped in `FallbackProvider`, which swallows exceptions and retries with `MockProvider`.

OpenAI and Anthropic adapters use `httpx` against their HTTP APIs. Missing keys or HTTP errors trip the fallback.

## Runtime extras (not in the README)

In-memory TTL cache, per-client rate limiting, env-driven flags, admin routes under `/internal`, and a periodic chunk TTL purge. Details are in `HIDDEN_FEATURES.md` and `CONFIGURATION.md`.
