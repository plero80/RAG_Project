from app.ingestion.parser import parse_pdf
from app.ingestion.cleaner import clean_pages
from app.ingestion.chunker import chunk_pages
from app.ingestion.embedder import embed_chunks


raw_pages = parse_pdf("data/apple.pdf")

cleaned_pages = clean_pages(raw_pages)

chunks = chunk_pages(
    cleaned_pages,
    chunk_size=300,
    overlap=50
)


# ONLY embed the first 2 chunks for testing
test_chunks = chunks[:2]

embedded_chunks = embed_chunks(test_chunks)


for chunk in embedded_chunks:

    print("\n============================")
    print(f"Document: {chunk['document']}")
    print(f"Page: {chunk['page']}")
    print(f"Chunk ID: {chunk['chunk_id']}")

    print("\nText:")
    print(chunk["text"][:300])

    print("\nEmbedding length:")
    print(len(chunk["embedding"]))

    print("\nFirst 10 embedding values:")
    print(chunk["embedding"][:10])