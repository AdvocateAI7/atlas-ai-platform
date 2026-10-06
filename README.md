# atlas_ai_platform

A production-style AI backend built with FastAPI, SQLite, and SQLAlchemy. Supports chat completions, document ingestion, and retrieval-augmented generation (RAG), with a pluggable LLM provider layer that runs fully offline using a built-in mock provider.

---

## Features

### Public endpoints
| Endpoint | Description |
|---|---|
| `POST /chat` | Send a message to the configured LLM provider and receive a reply. Responses are cached by default. |
| `POST /documents` | Ingest text, chunk it, embed each chunk, and store it for retrieval. |
| `POST /ask` | Answer a question using stored document chunks as context (RAG). |
| `GET /health` | Liveness check. |

### Internal / admin endpoints
| Endpoint | Description |
|---|---|
| `GET /internal/stats` | Usage statistics: document count, chunk count, cache hits/misses. |
| `POST /internal/cache/flush` | Evict all cached responses. |

Protected by the `X-Internal-Token` header. Set `INTERNAL_ADMIN_TOKEN` in your environment — the routes return 503 if the token is not configured.

### Hidden / undocumented behaviours (now documented)
- **In-memory response cache** — repeated `/chat` calls with identical message, temperature, and provider are served from cache. TTL is `CACHE_TTL_SECONDS` (default 300 s). Disable with `ENABLE_RESPONSE_CACHE=false`.
- **Per-client rate limiter** — keyed by the optional `X-Client-Id` header (falls back to `"anonymous"`). Default: 30 requests per 60 s. Tune with `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`.
- **Provider fallback** — if the configured primary provider raises an exception, the request is transparently retried against the mock provider. The `provider` field in the response will show `"fallback"`.
- **Feature flags** — `ENABLE_RESPONSE_CACHE`, `ENABLE_PROMPT_LOGGING`, `STRICT_MODE` alter runtime behaviour (see [docs/CONFIGURATION.md](docs/CONFIGURATION.md)).
- **Background cleanup** — a background task runs every `CLEANUP_INTERVAL_SECONDS` and purges chunks older than `CHUNK_TTL_SECONDS`.
- **Prompt logging** — when `ENABLE_PROMPT_LOGGING=true`, sanitised (redacted + truncated) prompt excerpts are appended to `PROMPT_LOG_PATH`.

---

## Setup

### Prerequisites
- Python 3.11+
- Docker (optional)

### Local

```bash
git clone <repo>
cd atlas-ai-platform

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — at minimum set INTERNAL_ADMIN_TOKEN

uvicorn app.main:app --reload
```

### Docker Compose

```bash
cp .env.example .env
# Edit .env

docker compose up --build
```

The API is available at `http://localhost:8000`.

---

## Configuration

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for a complete list of environment variables, their defaults, and effects.

---

## Usage examples

**Chat**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is retrieval-augmented generation?", "temperature": 0.3}'
```

**Ingest a document**
```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"text": "RAG combines a retrieval step with generation to ground LLM answers in source material.", "source": "intro"}'
```

**Ask a question**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How does RAG work?"}'
```

**Admin: view stats**
```bash
curl http://localhost:8000/internal/stats \
  -H "X-Internal-Token: <your-token>"
```

**Admin: flush cache**
```bash
curl -X POST http://localhost:8000/internal/cache/flush \
  -H "X-Internal-Token: <your-token>"
```

---

## Testing

```bash
python -m pytest tests/ -v
```

The suite covers all public endpoints, the internal admin routes, rate limiting, cache correctness, provider fallback, feature flags, and chunking edge cases (40 tests).

---

## Selecting an LLM provider

Set `LLM_PROVIDER` to one of:

| Value | Notes |
|---|---|
| `mock` (default) | No API key required. Returns labelled placeholder text. |
| `openai` | Requires `OPENAI_API_KEY`. Uses `OPENAI_MODEL` (default `gpt-4o-mini`). |
| `anthropic` | Requires `ANTHROPIC_API_KEY`. Uses `ANTHROPIC_MODEL` (default `claude-3-5-sonnet-20241022`). |

If the configured provider fails at runtime the mock provider is used as a fallback automatically.

---

## Project documentation

| Document | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Structure, request flow, data model |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Full endpoint reference with examples |
| [docs/HIDDEN_FEATURES.md](docs/HIDDEN_FEATURES.md) | Undocumented behaviours and environment triggers |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | All environment variables |
| [docs/ISSUES_FOUND.md](docs/ISSUES_FOUND.md) | Bugs and security findings with resolution status |
