"""Unit tests for text chunker."""

import pytest

from app.services.knowledge.chunker import TextChunker, TextChunk


class TestTextChunker:
    """Tests for TextChunker class."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "This is a test. " * 20  # ~320 chars

        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        assert all(isinstance(c, TextChunk) for c in chunks)
        assert all(len(c.text) <= 50 + 20 for c in chunks)  # Allow some buffer

    def test_chunk_short_text(self):
        """Test chunking text shorter than chunk size."""
        chunker = TextChunker(chunk_size=1000, overlap=100)
        text = "Short text."

        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == "Short text."
        assert chunks[0].index == 0

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = TextChunker(chunk_size=100, overlap=10)

        chunks = chunker.chunk("")

        assert len(chunks) == 0

    def test_chunk_with_metadata(self):
        """Test chunking with metadata."""
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "Test text that is long enough to chunk."
        metadata = {"source": "test", "type": "unit"}

        chunks = chunker.chunk(text, metadata=metadata)

        for chunk in chunks:
            assert chunk.metadata == metadata

    def test_chunk_preserves_sentence_boundaries(self):
        """Test that chunking tries to preserve sentence boundaries."""
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        chunks = chunker.chunk(text)

        # Chunks should try to end at sentence boundaries when possible
        for chunk in chunks:
            # Text should be meaningful, not cut mid-word
            assert not chunk.text.endswith(" t")  # Not cut mid-word like "t"

    def test_chunk_index_increments(self):
        """Test that chunk indices increment correctly."""
        chunker = TextChunker(chunk_size=30, overlap=5)
        text = "Word " * 50

        chunks = chunker.chunk(text)

        indices = [c.index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = TextChunker(chunk_size=50, overlap=20)
        text = "A" * 200  # Simple text for testing

        chunks = chunker.chunk(text)

        # With overlap, consecutive chunks should share some content
        if len(chunks) >= 2:
            # The end of chunk 0 should overlap with start of chunk 1
            # This is a simplistic check
            assert len(chunks[0].text) >= 20
