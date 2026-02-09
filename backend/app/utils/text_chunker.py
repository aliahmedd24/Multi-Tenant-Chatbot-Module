"""Text chunking for knowledge base documents."""

import re


def chunk_text(
    text: str,
    chunk_size: int = 400,
    chunk_overlap: int = 50,
) -> list[dict]:
    """Split text into overlapping chunks of approximately chunk_size words.

    Uses sentence-boundary splitting to avoid breaking mid-sentence.
    Token count is approximated by word count.

    Returns list of dicts: [{content, token_count, index}, ...]
    """
    if not text or not text.strip():
        return []

    # Split into sentences (on period, exclamation, question mark, or double newline)
    sentences = re.split(r'(?<=[.!?])\s+|\n{2,}', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    chunks = []
    current_sentences: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        word_count = len(sentence.split())

        # If a single sentence exceeds chunk_size, add it as its own chunk
        if word_count > chunk_size and not current_sentences:
            chunks.append(sentence)
            continue

        # If adding this sentence would exceed chunk_size, finalize current chunk
        if current_word_count + word_count > chunk_size and current_sentences:
            chunks.append(" ".join(current_sentences))

            # Calculate overlap: keep trailing sentences up to chunk_overlap words
            overlap_sentences: list[str] = []
            overlap_count = 0
            for s in reversed(current_sentences):
                s_words = len(s.split())
                if overlap_count + s_words > chunk_overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_count += s_words

            current_sentences = overlap_sentences
            current_word_count = overlap_count

        current_sentences.append(sentence)
        current_word_count += word_count

    # Don't forget the last chunk
    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return [
        {
            "content": chunk,
            "token_count": len(chunk.split()),
            "index": i,
        }
        for i, chunk in enumerate(chunks)
    ]
