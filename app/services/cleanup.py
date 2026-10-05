import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.models import Chunk

logger = logging.getLogger(__name__)


def purge_expired_chunks() -> int:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.chunk_ttl_seconds)
    db = SessionLocal()
    try:
        result = db.execute(delete(Chunk).where(Chunk.created_at < cutoff))
        db.commit()
        deleted = result.rowcount or 0
        if deleted:
            logger.info("purged %s expired chunks", deleted)
        return deleted
    finally:
        db.close()
