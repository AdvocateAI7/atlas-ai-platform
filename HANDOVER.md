# Handover walkthrough

This is a brief call script for a 15-minute client demo. Run each command in a terminal with the server already started (`uvicorn app.main:app --reload`).

---

## 1. Start and health check (1 min)

```bash
uvicorn app.main:app --reload
curl http://localhost:8000/health
# → {"status":"ok"}
```

Confirm the service starts cleanly and the health endpoint responds.

---

## 2. Chat completions (2 min)

```bash
# Basic request (mock provider, no API key needed)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain caching in one sentence.", "temperature": 0.3}'

# Same request a second time → provider: "cache", cached: true
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain caching in one sentence.", "temperature": 0.3}'
```

Point out: the second call is served from the in-memory cache. The `provider` field changes to `"cache"` and `cached` is `true`.

---

## 3. Document ingest and RAG (3 min)

```bash
# Ingest a document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"text": "The atlas_ai_platform supports RAG: it chunks documents, embeds them, and retrieves relevant passages to ground LLM answers.", "source": "demo"}'
# → {"id":1,"source":"demo","chunks":1}

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How does RAG work in this platform?"}'
# → {"answer":"...","chunk_ids":[1],"provider":"mock"}
```

Show that `chunk_ids` contains the ID of the ingested chunk, confirming retrieval worked.

---

## 4. Internal admin routes (2 min)

```bash
# Without token → 503
curl http://localhost:8000/internal/stats

# With correct token (set INTERNAL_ADMIN_TOKEN=demo-secret in .env)
curl http://localhost:8000/internal/stats \
  -H "X-Internal-Token: demo-secret"
# → {"documents":1,"chunks":1,"cache_size":1,"cache_hits":1,"cache_misses":1}

# Flush the cache
curl -X POST http://localhost:8000/internal/cache/flush \
  -H "X-Internal-Token: demo-secret"
# → {"flushed":1}
```

---

## 5. Rate limiting (1 min)

```bash
# Rapid-fire requests from the same client
for i in 1 2 3; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -H "X-Client-Id: demo-client" \
    -d '{"message": "rate limit test '$i'"}'
done
```

Default limit is 30 req / 60 s. Lower it in `.env` (`RATE_LIMIT_MAX_REQUESTS=2`) to demonstrate a 429 response.

---

## 6. Test suite (2 min)

```bash
pytest tests/ -v
# 40 passed
```

Walk through the test file names briefly: chunking regression, cache key fix, admin auth, rate limiting, fallback, flags.

---

## 7. Docker (2 min)

```bash
docker compose up --build
curl http://localhost:8000/health
```

Show the container starting cleanly. Point out the `.env.example` file and the volume mounts for the database and logs.

---

## 8. Wrap-up (2 min)

Point the client to:

- `docs/HIDDEN_FEATURES.md` — everything that was undocumented
- `docs/ISSUES_FOUND.md` — all findings with resolution status and commit refs
- `PR_DESCRIPTION.md` — suggested next steps (Redis, log rotation, real embeddings)
