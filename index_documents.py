from app.parsing import (
    docx_parser,
    pdf_parser
)

from app.chunking import strategies

from app.ingestion.cleaner import clean_pages
from app.ingestion.embedder import embed_chunks
import argparse
from pathlib import Path


from app.db.database import (
    init_db,
    insert_chunks
)


DOCUMENT_TYPES = {
    "docx" : docx_parser.DOCXParser(),
    "pdf" : pdf_parser.PDFParser()
}


STRATEGIES = {
    "fixed-size" : strategies.FixedSizeChunker,
    "sentence" : strategies.SentenceChunker,
    "paragraph": strategies.ParagraphChunker
}


def main():

    parser = argparse.ArgumentParser(description="Process PDF documents")

    parser.add_argument("--file", type=str, required=True, help="Path to PDF/DOCX file")

    parser.add_argument("--strategy", type=int, required=True, choices=["fixed-size","sentence","paragraph"])

    parser.add_argument("--chunk-size", type=int, default=500)

    parser.add_argument("--overlap", type=int, default=50)

    args = parser.parse_args()

    path = Path(args.file)

    type_document = path.suffix.lower()

    if type_document not in DOCUMENT_TYPES.keys():
        raise ValueError("not supported document")

    parser = DOCUMENT_TYPES[type_document]







if __name__ == "__main__":
    main()