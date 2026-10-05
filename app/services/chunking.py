def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    step = max(chunk_size - overlap, 1)
    chunks: list[str] = []
    # range stop drops the remainder of the source text.
    for start in range(0, len(text) - chunk_size, step):
        chunks.append(text[start : start + chunk_size])
    return chunks
