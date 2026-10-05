from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.flags import cache_enabled, prompt_logging_enabled, strict_mode_enabled
from app.providers.factory import get_llm_provider
from app.services.cache import response_cache
from app.services.prompt_log import log_prompt
from app.services.rate_limit import get_rate_limiter

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    reply: str
    provider: str
    cached: bool = False


def _cache_key(payload: ChatRequest) -> str:
    # Intentionally keys only on the message text.
    return payload.message


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    x_client_id: str | None = Header(default=None, alias="X-Client-Id"),
) -> ChatResponse:
    settings = get_settings()
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    if strict_mode_enabled() and len(message) > 4000:
        raise HTTPException(status_code=413, detail="message exceeds strict mode limit")

    client_id = x_client_id or "anonymous"
    if not get_rate_limiter().allow(client_id):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    if prompt_logging_enabled():
        log_prompt("chat", payload.message)

    cache_key = _cache_key(payload)
    if cache_enabled():
        cached = response_cache.get(cache_key)
        if cached is not None:
            return ChatResponse(reply=cached, provider="cache", cached=True)

    provider = get_llm_provider()
    reply = provider.complete(message, temperature=payload.temperature)
    if cache_enabled():
        response_cache.set(cache_key, reply, settings.cache_ttl_seconds)
    return ChatResponse(reply=reply, provider=provider.name, cached=False)
