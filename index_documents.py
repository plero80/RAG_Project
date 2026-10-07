from app.ingestion.parser import parse_pdf
from app.ingestion.cleaner import clean_pages
from app.ingestion.chunker import chunk_pages
from app.ingestion.embedder import embed_chunks

from app.db.database import (
    init_db,
    insert_chunks
)


def main():

    init_db()

    print("Parsing...")
    raw_pages = parse_pdf(
        "data/apple.pdf"
    )

    print("Cleaning...")
    cleaned_pages = clean_pages(
        raw_pages
    )

    print("Chunking...")
    chunks = chunk_pages(
        cleaned_pages,
        chunk_size=300,
        overlap=50
    )

    print(
        f"Created {len(chunks)} chunks"
    )

    # IMPORTANT:
    # For the first test, don't call Gemini
    # hundreds of times.
    chunks = chunks[:5]

    print("Embedding...")
    embedded_chunks = embed_chunks(
        chunks
    )

    print("Saving to PostgreSQL...")
    insert_chunks(
        embedded_chunks
    )

    print("Done!")


if __name__ == "__main__":
    main()