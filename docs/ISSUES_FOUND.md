# Issues found

Severity: High / Medium / Low.

## ISS-1 — Last document remainder is never stored

- Severity: High
- Where: `app/services/chunking.py::chunk_text`
- `range(0, len(text) - chunk_size, step)` never emits a window that includes the tail of the source. Text after the last full window is dropped, so RAG cannot retrieve the end of a document.
- Suggested fix: advance `start` until the string is consumed; on the last window take `text[start:]` (or pad/overlap consistently). Add a unit test with length `chunk_size + 1`.

## ISS-2 — Chat cache key ignores temperature

- Severity: Medium
- Where: `app/api/chat.py::_cache_key`
- Repeated `/chat` calls with the same `message` but a different `temperature` reuse the first reply. The mock provider embeds temperature in the text, which makes the mismatch obvious.
- Suggested fix: include `temperature` (and provider identity if it can change) in the cache key.

## ISS-3 — Internal admin token compared with `==` and defaults to empty

- Severity: High
- Where: `app/api/internal.py::_require_admin`
- Plain string equality is not constant-time. `INTERNAL_ADMIN_TOKEN` defaults to `""`, and a missing header is coerced to `""`, so `/internal/*` is open unless an operator sets a secret.
- Suggested fix: require a non-empty configured token; compare with `hmac.compare_digest`; return 401 if either side is empty.

## ISS-4 — Prompt logging writes raw user text

- Severity: High
- Where: `app/services/prompt_log.py::log_prompt`; callers in `chat`, `documents`, `ask`
- When `ENABLE_PROMPT_LOGGING` is true, full messages (API keys, PII, customer content) are appended to `logs/prompts.log` with no redaction or rotation.
- Suggested fix: redact obvious secret patterns, truncate, and keep the log behind the same admin controls as `/internal`. Default should remain off.

## ISS-5 — Inconsistent error handling

- Severity: Medium
- Where: `app/api/chat.py` (`HTTPException`), `app/api/documents.py` (`JSONResponse` with `message` / `error` / `failed` keys), `app/api/ask.py` (HTTP 200 + `{ok: false}`)
- Clients cannot rely on status codes or a single error schema. `/ask` failures look like success to HTTP-aware monitors.
- Suggested fix: one exception type and handler that always returns `{ "detail": "...", "code": "..." }` with the correct status.

## ISS-6 — Thin test coverage

- Severity: Medium
- Where: `tests/test_health.py`, `tests/test_chat.py`
- No tests for ingest, RAG, internal auth, cache, rate limits, fallback, cleanup, or the chunker off-by-one.
- Suggested fix: TestClient coverage per endpoint and per hidden behavior, with settings overrides so rate limits and flags are deterministic.

## ISS-7 — Fallback hides provider outages

- Severity: Low
- Where: `app/providers/factory.py::FallbackProvider.complete`
- Primary failures are logged and then served as mock text with HTTP 200. Operators may not notice billing/key issues. `provider` reports `fallback`, which is easy to miss.
- Suggested fix: keep the fallback for resilience, but surface it in metrics/stats and optionally a warning field on the response.

## ISS-8 — Rate limiter and cache are process-local

- Severity: Low
- Where: `app/services/rate_limit.py`, `app/services/cache.py`
- Multiple workers do not share state; limits and cache hits are per process. Document this or move to Redis if the service is scaled out.
