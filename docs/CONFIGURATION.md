# Configuration

Settings are loaded from environment variables and an optional `.env` file (`app/core/config.py::Settings`). `get_settings()` is cached for the process lifetime; restart after changes.

| Variable | Default | Effect |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./atlas.db` | SQLAlchemy URL |
| `LLM_PROVIDER` | `mock` | `mock`, `openai`, or `anthropic` |
| `OPENAI_API_KEY` | empty | Required for a real OpenAI call; missing/invalid values fall back to mock |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model name |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API root |
| `ANTHROPIC_API_KEY` | empty | Required for a real Anthropic call |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Message model name |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | API root |
| `ENABLE_RESPONSE_CACHE` | `true` | In-memory `/chat` cache |
| `ENABLE_PROMPT_LOGGING` | `false` | Write raw prompts to `PROMPT_LOG_PATH` |
| `STRICT_MODE` | `false` | Tighter size limits on `/chat` and `/documents` |
| `INTERNAL_ADMIN_TOKEN` | empty | Shared secret for `/internal/*`. Empty token + missing header currently authorizes |
| `RATE_LIMIT_MAX_REQUESTS` | `30` | `/chat` requests per window per client id |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Limiter window |
| `CACHE_TTL_SECONDS` | `300` | Chat cache entry lifetime |
| `CHUNK_SIZE` | `400` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap passed into the chunker |
| `CHUNK_TTL_SECONDS` | `604800` | Age after which the cleanup task deletes chunks |
| `CLEANUP_INTERVAL_SECONDS` | `3600` | Sleep between cleanup runs (floor 5s) |
| `RAG_TOP_K` | `3` | Chunks injected into `/ask` |
| `EMBEDDING_DIMS` | `64` | Local hash-embedding size |
| `PROMPT_LOG_PATH` | `logs/prompts.log` | Prompt log file when logging is enabled |

Boolean env values follow pydantic-settings (`true`/`false`, `1`/`0`).
