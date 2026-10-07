from app.ingestion.parser import parse_pdf
from app.ingestion.cleaner import clean_text


raw_pages = parse_pdf("data/apple.pdf")

page = raw_pages[5]

raw_text = page["text"]
cleaned_text = clean_text(raw_text)


print(f"DOCUMENT: {page['document']}")
print(f"PAGE: {page['page']}")

print("\n===== RAW =====")
print(raw_text[:1500])

print("\n===== CLEANED =====")
print(cleaned_text[:1500])