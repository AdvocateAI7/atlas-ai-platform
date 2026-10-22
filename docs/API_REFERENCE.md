# API reference

Base URL: `http://localhost:8000`. JSON request bodies. FastAPI also serves `/docs`.

## GET /health

Liveness check. No auth.

Request:

```
GET /health
```

Response `200`:

```json
{ "status": "ok" }
```

## POST /chat

Generate a reply. Optional headers: `X-Client-Id` (rate-limit bucket).

Request:

```json
{ "message": "Summarize the release notes", "temperature": 0.2 }
```

`temperature` is optional, 0–2, default `0.2`.

Response `200`:

```json
{
  "reply": "[mock t=0.20] I received your request ...",
  "provider": "mock",
  "cached": false
}
```

A cache hit uses `"provider": "cache"` and `"cached": true`.

Errors:

- `400` `{ "detail": "message is required" }` — empty/whitespace message
- `413` `{ "detail": "message exceeds strict mode limit" }` — `STRICT_MODE` and length > 4000
- `422` — validation (missing `message`, temperature out of range)
- `429` `{ "detail": "rate limit exceeded" }`

## POST /documents

Ingest text, chunk it, store embeddings.

Request:

```json
{ "text": "Atlas indexes operator runbooks for later retrieval.", "source": "runbook" }
```

`source` is optional (default `"upload"`).

Response `200`:

```json
{ "id": 1, "source": "runbook", "chunks": 1 }
```

Errors (inconsistent shapes):

- `400` `{ "message": "text missing" }`
- `400` `{ "error": "payload too large" }` — strict mode, length > 20000
- `500` `{ "failed": "<exception>" }`

## POST /ask

Retrieve similar chunks and answer with that context.

Request:

```json
{ "question": "What does Atlas index?" }
```

Success `200`:

```json
{
  "ok": true,
  "answer": "[mock t=0.20] ...",
  "chunk_ids": [1],
  "provider": "mock"
}
```

Failure is still HTTP `200`:

```json
{ "ok": false, "error": "question is required" }
```

## GET /internal/stats

Header: `X-Internal-Token: <INTERNAL_ADMIN_TOKEN>`.

Response `200`:

```json
{
  "documents": 1,
  "chunks": 3,
  "cache_size": 1,
  "cache_hits": 4,
  "cache_misses": 2
}
```

`401` `{ "detail": "unauthorized" }` when the token does not match.

## POST /internal/cache/flush

Same auth header.

Response `200`:

```json
{ "flushed": 1 }
```

`flushed` is the number of cache entries removed.
