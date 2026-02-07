"""Text chunking service.

Splits documents into smaller chunks for embedding and retrieval.
"""

from dataclasses import dataclass
from typing import Optional

import structlog


logger = structlog.get_logger()


@dataclass
class TextChunk:
    """Represents a text chunk."""

    text: str
    index: int
    start_char: int
    end_char: int
    metadata: Optional[dict] = None


class TextChunker:
    """Splits text into overlapping chunks for embedding.

    Uses character-based chunking with configurable size and overlap.

    Usage:
        chunker = TextChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk(text)
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        min_chunk_size: int = 100,
    ):
        """Initialize chunker.

        Args:
            chunk_size: Target size of each chunk in characters.
            overlap: Number of overlapping characters between chunks.
            min_chunk_size: Minimum chunk size (to avoid tiny final chunks).
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def chunk(
        self,
        text: str,
        metadata: Optional[dict] = None,
    ) -> list[TextChunk]:
        """Split text into chunks.

        Args:
            text: Text to chunk.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            List of TextChunk objects.
        """
        if not text or not text.strip():
            return []

        logger.info("chunk_start", text_length=len(text))

        chunks = []
        start = 0
        index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If we're near the end, include remaining text
            if end >= len(text):
                end = len(text)
            else:
                # Try to break at sentence or paragraph boundary
                end = self._find_break_point(text, start, end)

            chunk_text = text[start:end].strip()

            # Only add if chunk is large enough
            if len(chunk_text) >= self.min_chunk_size or end >= len(text):
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                        metadata=metadata,
                    )
                )
                index += 1

            # Move start position (with overlap)
            start = end - self.overlap
            if start <= chunks[-1].start_char if chunks else 0:
                start = end  # Avoid infinite loop

        logger.info("chunk_complete", chunk_count=len(chunks))
        return chunks

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find a natural break point near the target end position.

        Prefers paragraph breaks, then sentence breaks, then word breaks.

        Args:
            text: Full text.
            start: Start of current chunk.
            end: Target end position.

        Returns:
            Adjusted end position.
        """
        # Look for paragraph break (double newline)
        for i in range(end, max(start, end - 200), -1):
            if i < len(text) - 1 and text[i : i + 2] == "\n\n":
                return i + 2

        # Look for sentence break (period, exclamation, question)
        for i in range(end, max(start, end - 100), -1):
            if i < len(text) and text[i] in ".!?" and (i + 1 >= len(text) or text[i + 1] in " \n"):
                return i + 1

        # Look for word break (space)
        for i in range(end, max(start, end - 50), -1):
            if i < len(text) and text[i] == " ":
                return i + 1

        return end

    def chunk_with_separators(
        self,
        text: str,
        separators: list[str] = ["\n\n", "\n", ". ", " "],
    ) -> list[TextChunk]:
        """Chunk text using recursive separators.

        Tries each separator in order, falling back to next if chunks are still too large.

        Args:
            text: Text to chunk.
            separators: List of separators to try.

        Returns:
            List of TextChunk objects.
        """
        return self._recursive_chunk(text, separators, 0)

    def _recursive_chunk(
        self,
        text: str,
        separators: list[str],
        index: int,
    ) -> list[TextChunk]:
        """Recursively chunk text with separators."""
        if not text.strip():
            return []

        if len(text) <= self.chunk_size:
            return [
                TextChunk(
                    text=text.strip(),
                    index=index,
                    start_char=0,
                    end_char=len(text),
                )
            ]

        if not separators:
            # Fall back to character-based chunking
            return self.chunk(text)

        separator = separators[0]
        parts = text.split(separator)
        chunks = []
        current_chunk = ""
        current_index = index

        for part in parts:
            if len(current_chunk) + len(part) + len(separator) <= self.chunk_size:
                current_chunk += (separator if current_chunk else "") + part
            else:
                if current_chunk:
                    chunks.append(
                        TextChunk(
                            text=current_chunk.strip(),
                            index=current_index,
                            start_char=0,
                            end_char=len(current_chunk),
                        )
                    )
                    current_index += 1
                current_chunk = part

        if current_chunk:
            chunks.append(
                TextChunk(
                    text=current_chunk.strip(),
                    index=current_index,
                    start_char=0,
                    end_char=len(current_chunk),
                )
            )

        return chunks
