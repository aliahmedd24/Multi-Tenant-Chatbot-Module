"""Tests for the text chunker utility."""

from app.utils.text_chunker import chunk_text


def test_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   ") == []
    assert chunk_text(None) == []


def test_single_short_sentence():
    result = chunk_text("Hello world.", chunk_size=10)
    assert len(result) == 1
    assert result[0]["content"] == "Hello world."
    assert result[0]["token_count"] == 2
    assert result[0]["index"] == 0


def test_chunks_respect_size_limit():
    # Create text with many sentences, each ~5 words
    sentences = ["This is sentence number {}.".format(i) for i in range(20)]
    text = " ".join(sentences)

    result = chunk_text(text, chunk_size=20, chunk_overlap=0)

    for chunk in result:
        # Allow small overshoot due to sentence-boundary splitting
        assert chunk["token_count"] <= 25, (
            f"Chunk {chunk['index']} has {chunk['token_count']} words"
        )


def test_chunks_have_sequential_indices():
    sentences = ["Sentence number {}.".format(i) for i in range(30)]
    text = " ".join(sentences)
    result = chunk_text(text, chunk_size=15, chunk_overlap=0)

    for i, chunk in enumerate(result):
        assert chunk["index"] == i


def test_overlap_creates_shared_content():
    # Create enough text to produce multiple chunks
    sentences = ["Word{} is here.".format(i) for i in range(20)]
    text = " ".join(sentences)

    result = chunk_text(text, chunk_size=10, chunk_overlap=5)

    # With overlap, later chunks should share some content with previous ones
    if len(result) >= 2:
        words_0 = set(result[0]["content"].split())
        words_1 = set(result[1]["content"].split())
        assert words_0 & words_1, "Overlapping chunks should share some words"


def test_large_single_sentence():
    # A single sentence that exceeds chunk_size
    words = ["word"] * 500
    text = " ".join(words) + "."
    result = chunk_text(text, chunk_size=100)

    assert len(result) >= 1
    assert result[0]["token_count"] > 100


def test_paragraph_splitting():
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
    result = chunk_text(text, chunk_size=100)

    assert len(result) >= 1
    # All content should be present
    combined = " ".join(c["content"] for c in result)
    assert "First paragraph" in combined
    assert "Second paragraph" in combined
    assert "Third paragraph" in combined


def test_token_count_matches_word_count():
    text = "The quick brown fox jumps. Over the lazy dog."
    result = chunk_text(text, chunk_size=100)

    for chunk in result:
        actual_words = len(chunk["content"].split())
        assert chunk["token_count"] == actual_words
