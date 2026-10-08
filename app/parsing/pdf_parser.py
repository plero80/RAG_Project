from base import DocumentParser
import pymupdf as fitz
from pathlib import Path

class PDFParser(DocumentParser):

    def parse(self, pdf_path: str) -> list[dict]:

        pages = []
        document_name = Path(pdf_path).name

        with fitz.open(pdf_path) as pdf:

            for page_number, page in enumerate(pdf, start=1):

                blocks = []

                for block in page.get_text("blocks", sort=True):

                    x0, y0, x1, y1, text, block_no, block_type = block[:7]

                    if block_type != 0:
                        continue

                    blocks.append({
                        "text": text,
                        "bbox": (x0, y0, x1, y1)
                    })

                pages.append({
                    "document_id": self.document_id,
                    "document_name": document_name,
                    "page_number": page_number,
                    "text": page.get_text("text", sort=True),
                    "blocks": blocks
                })

        return pages