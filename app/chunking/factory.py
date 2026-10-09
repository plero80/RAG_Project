from .base import ChunkingStrategy
from .strategies import (
    FixedSizeChunker,
    SentenceChunker,
    ParagraphChunker,
)


def create_chunker(
    strategy: str,
    chunk_size: int,
    overlap: int,
) -> ChunkingStrategy:

    if strategy == "fixed-size":
        return FixedSizeChunker(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )

    if strategy == "sentence":
        return SentenceChunker(max_chars=chunk_size)

    if strategy == "paragraph":
        return ParagraphChunker()

    raise ValueError(f"Unsupported chunking strategy: {strategy}")