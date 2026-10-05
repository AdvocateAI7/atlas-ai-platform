from app.core.config import get_settings


def cache_enabled() -> bool:
    return get_settings().enable_response_cache


def prompt_logging_enabled() -> bool:
    return get_settings().enable_prompt_logging


def strict_mode_enabled() -> bool:
    return get_settings().strict_mode
