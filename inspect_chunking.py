from app.ingestion.parser import parse_pdf
from app.ingestion.cleaner import clean_pages
from app.ingestion.chunker import chunk_pages


raw_pages = parse_pdf("data/apple.pdf")

cleaned_pages = clean_pages(raw_pages)

chunks = chunk_pages(
    cleaned_pages,
    chunk_size=300,
    overlap=50
)


print(f"Pages: {len(cleaned_pages)}")
print(f"Chunks: {len(chunks)}")


print("\n===== CHUNK 0 =====")
print(chunks[0])


print("\n===== CHUNK 1 =====")
print(chunks[1])