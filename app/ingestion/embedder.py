from google import genai
from google.genai import types
from dotenv import load_dotenv
from contextlib import nullcontext

from app.core.tracer import IndexingTracer


load_dotenv()

client = genai.Client(
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=6,
            initial_delay=5,
            max_delay=60,
            http_status_codes=[429, 500, 502, 503, 504],
        )
    )
)

MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768


def embed_document(text: str, title: str | None = None) -> list[float]:

    if not text.strip():
        raise ValueError("Cannot embed empty text")

    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            title=title,
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
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


    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
    )

    embeddings = response.embeddings
    if not embeddings:
        raise ValueError("Gemini returned no embeddings")

    values = embeddings[0].values
    if not values:
        raise ValueError("Gemini returned no embedding values")

    return values


def embed_chunks(
    chunks: list[dict], tracer: IndexingTracer | None = None
) -> list[dict]:

    embedded_chunks = []

    for number, chunk in enumerate(chunks, start=1):
        progress = (
            tracer.stage(
                "embedding_chunk",
                heartbeat=True,
                chunk_number=number,
                chunk_count=len(chunks),
                completed_chunks=number - 1,
                chunk_id=chunk["chunk_id"],
                character_count=len(chunk["text"]),
                model=MODEL_NAME,
            )
            if tracer is not None else nullcontext({})
        )
        with progress as metadata:
            vector = embed_document(
                text=chunk["text"],
                title=chunk["document_name"]
            )
            metadata["completed_chunks"] = number
            metadata["dimensions"] = len(vector)

        embedded_chunks.append({
            **chunk,
            "embedding": vector
        })

    return embedded_chunks
