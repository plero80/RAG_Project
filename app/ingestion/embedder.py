from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()

client = genai.Client()

MODEL_NAME = "gemini-embedding-2"
EMBEDDING_DIMENSION = 768


def embed_document(text: str, title: str | None = None) -> list[float]:

    if not text.strip():
        raise ValueError("Cannot embed empty text")

    if title is None:
        title = "none"

    prepared_text = f"title: {title} | text: {text}"

    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=prepared_text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )

    embeddings = response.embeddings
    if not embeddings:
        raise ValueError("Gemini returned no embeddings")

    values = embeddings[0].values
    if not values:
        raise ValueError("Gemini returned no embedding values")

    return values


def embed_query(query: str) -> list[float]:

    if not query.strip():
        raise ValueError("Cannot embed empty query")

    prepared_query = (
        f"task: question answering | query: {query}"
    )

    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=prepared_query,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )

    embeddings = response.embeddings
    if not embeddings:
        raise ValueError("Gemini returned no embeddings")

    values = embeddings[0].values
    if not values:
        raise ValueError("Gemini returned no embedding values")

    return values


def embed_chunks(chunks: list[dict]) -> list[dict]:

    embedded_chunks = []

    for chunk in chunks:

        vector = embed_document(
            text=chunk["text"],
            title=chunk["document"]
        )

        embedded_chunks.append({
            **chunk,
            "embedding": vector
        })

    return embedded_chunks
