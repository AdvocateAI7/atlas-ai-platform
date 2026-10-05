from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.models import Chunk, Document
from app.services.cache import response_cache
from fastapi import Depends

router = APIRouter(prefix="/internal", tags=["internal"])


def _require_admin(x_internal_token: str | None) -> None:
    expected = get_settings().internal_admin_token
    provided = x_internal_token or ""
    if provided == expected:
        return
    raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/stats")
def usage_stats(
    db: Session = Depends(get_db),
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _require_admin(x_internal_token)
    documents = db.scalar(select(func.count()).select_from(Document)) or 0
    chunks = db.scalar(select(func.count()).select_from(Chunk)) or 0
    return {
        "documents": documents,
        "chunks": chunks,
        "cache_size": response_cache.size(),
        "cache_hits": response_cache.hits,
        "cache_misses": response_cache.misses,
    }


@router.post("/cache/flush")
def flush_cache(
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _require_admin(x_internal_token)
    removed = response_cache.flush()
    return {"flushed": removed}
