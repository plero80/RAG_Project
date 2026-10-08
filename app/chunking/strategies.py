
import re

from .base import ChunkingStrategy


class FixedSizeChunker(ChunkingStrategy):
    strategy_name = "fixed"

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if not 0 <= chunk_overlap < chunk_size:
            raise ValueError("Invalid chunk_overlap")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_page(self, page: dict) -> list[str]:
        text = page.get("text") or ""
        pieces = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            pieces.append(text[start:end])

            if end == len(text):
                break

            start = end - self.chunk_overlap

        return pieces


class SentenceChunker(ChunkingStrategy):
    strategy_name = "sentence"

    def __init__(self, max_chars: int = 500):
        if max_chars <= 0:
            raise ValueError("max_chars must be positive")

        self.max_chars = max_chars

    def _split_page(self, page: dict) -> list[str]:
        text = page.get("text") or ""
        text = " ".join(text.split())

        if not text:
            return []

        # Basic sentence boundary detection
        sentences = re.split(r"(?<=[.!?])\s+", text)

        pieces = []
        current = []
        current_length = 0

        for sentence in sentences:
            additional = len(sentence) + (1 if current else 0)

            if current and current_length + additional > self.max_chars:
                pieces.append(" ".join(current))
                current = []
                current_length = 0

            current_length += len(sentence) + (1 if current else 0)
            current.append(sentence)

        if current:
            pieces.append(" ".join(current))

        return pieces


class ParagraphChunker(ChunkingStrategy):
    strategy_name = "paragraph"

    def _split_page(self, page: dict) -> list[str]:
        blocks = page.get("blocks") or []

        # Prefer structural information from the parser
        if blocks:
            texts = [
                block.get("text", "")
                for block in blocks
                if isinstance(block, dict)
            ]
        else:
            texts = []

        # Fallback when blocks contain no usable text
        if not any(text.strip() for text in texts):
            texts = [page.get("text") or ""]

        paragraphs = []

        for text in texts:
            # Separate paragraphs on blank lines
            parts = re.split(r"\n\s*\n", text)

            for part in parts:
                if part.strip():
                    paragraphs.append(part.strip())

        return paragraphs
