from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./atlas.db"
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_base_url: str = "https://api.anthropic.com"

    enable_response_cache: bool = True
    enable_prompt_logging: bool = False
    strict_mode: bool = False

    internal_admin_token: str = ""

    rate_limit_max_requests: int = 30
    rate_limit_window_seconds: int = 60

    cache_ttl_seconds: int = 300

    chunk_size: int = 400
    chunk_overlap: int = 50
    chunk_ttl_seconds: int = 7 * 24 * 3600
    cleanup_interval_seconds: int = 3600
    rag_top_k: int = 3
    embedding_dims: int = 64

    prompt_log_path: str = "logs/prompts.log"


@lru_cache
def get_settings() -> Settings:
    return Settings()
