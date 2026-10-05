import hashlib
import json
import math
import struct

from app.core.config import get_settings


def embed_text(text: str) -> list[float]:
    dims = get_settings().embedding_dims
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    seed = digest
    while len(values) < dims:
        for i in range(0, len(seed) - 3, 4):
            raw = struct.unpack_from(">I", seed, i)[0]
            values.append((raw / 0xFFFFFFFF) * 2.0 - 1.0)
            if len(values) == dims:
                break
        seed = hashlib.sha256(seed).digest()
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def serialize_embedding(values: list[float]) -> str:
    return json.dumps(values)


def deserialize_embedding(payload: str) -> list[float]:
    return json.loads(payload)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))
