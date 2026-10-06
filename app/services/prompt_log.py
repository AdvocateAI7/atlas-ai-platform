import re
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings

_SECRET_PATTERN = re.compile(
    r"(Bearer\s+\S+|sk-[A-Za-z0-9]{10,}|api[_-]?key[=:\s]+\S+)",
    re.IGNORECASE,
)
_MAX_LENGTH = 200


def _redact(text: str) -> str:
    redacted = _SECRET_PATTERN.sub("[REDACTED]", text)
    if len(redacted) > _MAX_LENGTH:
        redacted = redacted[:_MAX_LENGTH] + "…"
    return redacted


def log_prompt(source: str, prompt: str) -> None:
    settings = get_settings()
    path = Path(settings.prompt_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).isoformat(timespec="seconds")
    safe = _redact(prompt)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{ts}\t{source}\t{safe}\n")
