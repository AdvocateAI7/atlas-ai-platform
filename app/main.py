import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ask import router as ask_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.internal import router as internal_router
from app.core.config import get_settings
from app.core.db import init_db
from app.core.errors import AppError, app_error_handler
from app.services.cleanup import purge_expired_chunks

logger = logging.getLogger(__name__)


async def _chunk_cleanup_loop() -> None:
    settings = get_settings()
    interval = max(settings.cleanup_interval_seconds, 5)
    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(purge_expired_chunks)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("chunk cleanup failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    task = asyncio.create_task(_chunk_cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="atlas_ai_platform", lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(ask_router)
app.include_router(internal_router)
