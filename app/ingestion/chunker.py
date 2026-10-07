


def chunk_text(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50
) -> list[str]:

    if overlap >= chunk_size:
        raise ValueError("overlap is higher then chunk_size")

    words = text.split(" ")
    start = 0
    chunks = []


    while start < len(words):

        chunk_words = words[start:start + chunk_size]

        chunk = " ".join(chunk_words)

        chunks.append(chunk)

        start = start + chunk_size - overlap

    return chunks



def chunk_pages(
    pages: list[dict],
    chunk_size: int = 300,
    overlap: int = 50
) -> list[dict]:

    all_chunks = []
    chunk_id = 0

    for page in pages: 

        text_chunks = chunk_text(page["text"], chunk_size, overlap)

        for text_chunk in text_chunks:

            all_chunks.append({
                "document": page["document"],
                "page": page["page"],
                "chunk_id": chunk_id,
                "text": text_chunk
            })

            chunk_id += 1


    return all_chunks