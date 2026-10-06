# Hidden features

These behaviors are implemented in code and are not described in the project README.

## 1. Internal admin routes

- Files: `app/api/internal.py` (`router`, `_require_admin`, `usage_stats`, `flush_cache`); mounted in `app/main.py`.
- Prefix: `/internal`
- Auth: header `X-Internal-Token` compared to `INTERNAL_ADMIN_TOKEN` with `==`. A missing header is treated as `""`. If the env var is unset, any request without a token is allowed.
- Trigger:
  - `GET /internal/stats` — document/chunk counts and cache hit/miss/size.
  - `POST /internal/cache/flush` — clears `response_cache`.
- Env: `INTERNAL_ADMIN_TOKEN`

## 2. Feature flags

- Files: `app/core/config.py::Settings`, `app/core/flags.py` (`cache_enabled`, `prompt_logging_enabled`, `strict_mode_enabled`).
- `ENABLE_RESPONSE_CACHE` (default true) — `/chat` reads and writes the in-memory cache.
- `ENABLE_PROMPT_LOGGING` (default false) — `/chat`, `/documents`, and `/ask` append the raw payload to `PROMPT_LOG_PATH`.
- `STRICT_MODE` (default false) — `/chat` rejects messages longer than 4000 chars (HTTP 413); `/documents` rejects text longer than 20000 chars (HTTP 400).
- Trigger: set the env vars and restart the process (`get_settings` is lru-cached).

## 3. In-memory response cache with TTL

- Files: `app/services/cache.py::ResponseCache`; used in `app/api/chat.py::chat` and `_cache_key`.
- Trigger: `POST /chat` twice with the same `message`. The second response sets `cached: true` and `provider: "cache"` while the entry is live.
- TTL: `CACHE_TTL_SECONDS` (default 300).
- Cache key is the message string only; `temperature` is ignored.
- Flush: `POST /internal/cache/flush`.

## 4. Per-client rate limiter

- Files: `app/services/rate_limit.py::RateLimiter.allow`, `get_rate_limiter`; enforced in `app/api/chat.py::chat`.
- Key: `X-Client-Id`, or `anonymous` if omitted.
- Default: 30 requests per 60 seconds (`RATE_LIMIT_MAX_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`).
- Trigger: send more than 30 `POST /chat` calls in a minute with the same client id; response is HTTP 429 `{ "detail": "rate limit exceeded" }`.
- Applies to `/chat` only.

## 5. Background chunk cleanup

- Files: `app/main.py::_chunk_cleanup_loop`; `app/services/cleanup.py::purge_expired_chunks`.
- Started on app lifespan; sleeps `CLEANUP_INTERVAL_SECONDS` (minimum 5, default 3600) then deletes `Chunk` rows older than `CHUNK_TTL_SECONDS` (default 7 days).
- Trigger: run the app long enough for one interval, or call `purge_expired_chunks()` directly in a shell. Parent `Document` rows are not deleted.

## 6. Silent mock fallback

- Files: `app/providers/factory.py::FallbackProvider.complete`, `get_llm_provider`.
- Trigger: set `LLM_PROVIDER=openai` or `anthropic` without a working key/network. The primary adapter raises; the factory logs a warning and returns a mock completion. Callers still get HTTP 200. `ChatResponse.provider` is `fallback` in that case (`FallbackProvider.name`).
