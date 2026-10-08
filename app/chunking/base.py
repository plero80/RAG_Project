
from abc import ABC, abstractmethod
from uuid import uuid5, NAMESPACE_URL


class ChunkingStrategy(ABC):

    strategy_name: str

    def chunk(self, pages: list[dict]) -> list[dict]:
        chunks = []

        for page in pages:
            pieces = self._split_page(page)

            for piece in pieces:
                text = piece.strip()

                if not text:
                    continue

                chunk_index = len(chunks)
                document_id = page["document_id"]

                # Stable ID for identical content and strategy
                key = (
                    f"{document_id}:{self.strategy_name}:"
                    f"{page.get('page_number')}:"
                    f"{chunk_index}:{text}"
                )
                chunk_id = str(uuid5(NAMESPACE_URL, key))

                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "document_name": page["document_name"],
                    "page_number": page.get("page_number"),
                    "chunk_index": chunk_index,
                    "strategy": self.strategy_name,
                    "text": text,
                })

        return chunks

    @abstractmethod
    def _split_page(self, page: dict) -> list[str]:
        pass
