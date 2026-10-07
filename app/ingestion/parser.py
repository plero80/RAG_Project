from pathlib import Path
import pymupdf as fitz  # PyMuPDF


def parse_pdf(file_path: str) -> list[dict]:
    """ Extract pdf pages and returns a list of dictionray with metadata and data page. """


    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("The pdf doesn't exists")

    if path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF")

    
    doc = fitz.open(file_path)


    pages = []


    for page_index, page in enumerate(doc):
        text = page.get_text()

        pages.append(
            {
                "document" : path.name,
                "text" : text.strip(),
                "page" : page_index + 1
            }
        )


    doc.close()


    return pages



def parse_directory(directory: str) -> list[dict]:

    directory_path = Path(directory)

    all_pages = []

    for pdf_path in directory_path.glob("*.pdf"):
        all_pages.extend(parse_pdf(pdf_path))

    return all_pages




if __name__ == "__main__":
    pages = parse_pdf("data/apple.pdf")

    print(f"Number of pages: {len(pages)}")

    print("PAGE 1:")
    print(pages[0]["text"][:1000])