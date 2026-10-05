from app.services.chunking import chunk_text


def test_empty_string():
    assert chunk_text("", 100, 10) == []


def test_short_text_returns_single_chunk():
    assert chunk_text("hello", 100, 10) == ["hello"]


def test_exact_chunk_size_returns_single_chunk():
    text = "a" * 100
    assert chunk_text(text, 100, 0) == [text]


def test_tail_is_not_dropped():
    # ISS-1: text longer than chunk_size by 1 must produce a second chunk
    text = "a" * 101
    chunks = chunk_text(text, 100, 0)
    assert len(chunks) == 2
    assert chunks[1] == "a"


def test_overlap():
    text = "abcdefghij"
    chunks = chunk_text(text, 4, 2)
    # step = 4 - 2 = 2; starts: 0, 2, 4, 6, 8
    assert chunks[0] == "abcd"
    assert chunks[1] == "cdef"


def test_full_text_reconstructed():
    text = "the quick brown fox jumps over the lazy dog"
    chunks = chunk_text(text, 10, 3)
    # every character in text must appear in at least one chunk
    reconstructed = set("".join(chunks))
    assert set(text).issubset(reconstructed)


def test_last_chunk_always_present():
    text = "x" * 350
    chunks = chunk_text(text, 400, 50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_remainder_chunk():
    text = "a" * 450
    chunks = chunk_text(text, 400, 50)
    assert len(chunks) == 2
    joined = chunks[0] + chunks[1][50:]  # account for overlap
    assert len(joined) == 450
