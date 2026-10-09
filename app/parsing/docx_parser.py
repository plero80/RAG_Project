from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from .base import DocumentParser, generate_document_id



class DOCXParser(DocumentParser):


    def parse(self, file_path: str) -> list[dict]:

        doc = Document(file_path)
        document_name = Path(file_path).name

        blocks = []

        for element in doc.iter_inner_content():

            if isinstance(element, Paragraph):

                text = element.text.strip()

                if not text:
                    continue
                
                style = element.style
                
                blocks.append({
                    "type": "paragraph",
                    "text": text,
                    "style": style.name if style is not None else None,
                })

            elif isinstance(element, Table):

                rows = []

                for row in element.rows:
                    rows.append(
                        " | ".join(cell.text for cell in row.cells)
                    )

                blocks.append({
                    "type": "table",
                    "text": "\n".join(rows)
                })

        return [{
            "document_id": generate_document_id(file_path),
            "document_name": document_name,
            "page_number": None,
            "text": "\n\n".join(block["text"] for block in blocks),
            "blocks": blocks
        }]