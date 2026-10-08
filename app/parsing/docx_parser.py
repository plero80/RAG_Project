from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from base import DocumentParser



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

                blocks.append({
                    "type": "paragraph",
                    "text": text,
                    "style": element.style.name
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
            "document_id": self.document_id,
            "document_name": document_name,
            "page_number": None,
            "text": "\n\n".join(block["text"] for block in blocks),
            "blocks": blocks
        }]