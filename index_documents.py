from app.parsing import (
    docx_parser,
    pdf_parser
)
from app.ingestion.cleaner import clean_pages
import argparse
from pathlib import Path
from app.db.database import (
    init_db,
    insert_chunks
)
from app.chunking.factory import create_chunker
from app.chunking.base import ChunkingStrategy
from app.core.tracer import IndexingTracer
import httpx
import psycopg
import pymupdf
from zipfile import BadZipFile

from docx.opc.exceptions import PackageNotFoundError
from google.genai.errors import APIError
from lxml.etree import XMLSyntaxError

DOCUMENT_TYPES = {
    "docx" : docx_parser.DOCXParser(),
    "pdf" : pdf_parser.PDFParser()
}


def main():

    # CLI
    parser = argparse.ArgumentParser(description="Process PDF documents")
    parser.add_argument("--file", type=str, required=True, help="Path to PDF/DOCX file")
    parser.add_argument("--strategy", type=str, required=True, choices=["fixed-size","sentence","paragraph"])
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=50)

    args = parser.parse_args()

    path = Path(args.file)

    if not path.is_file():
        parser.error(f"File does not exist or is not a regular file: {path}")

    document_type = path.suffix.lower().lstrip(".")

    if document_type not in DOCUMENT_TYPES:
        parser.error("Unsupported file type. Use PDF or DOCX.")

    try:
        chunker = create_chunker(
            strategy=args.strategy,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
    except ValueError as exc:
        parser.error(str(exc))

    tracer = IndexingTracer()
    print(f"Trace ID: {tracer.trace_id} (logs/traces.jsonl)", flush=True)
    try:
        with tracer.stage("total", filename=path.name, strategy=args.strategy) as run:
            count = _index_document(parser, path, chunker, tracer)
            run["chunk_count"] = count
    except KeyboardInterrupt:
        parser.exit(130, "Indexing interrupted. See the trace for the last active stage.\n")

    print(
        f"Indexed {path.name}: {count} chunks using '{args.strategy}'.",
        flush=True,
    )


def _index_document(
    parser: argparse.ArgumentParser,
    path: Path,
    chunker: ChunkingStrategy,
    tracer: IndexingTracer,
) -> int:
    document_parser = DOCUMENT_TYPES[path.suffix.lower().lstrip(".")]

    try:
        with tracer.stage("parse", heartbeat=True) as metrics:
            splits = document_parser.parse(str(path))
            metrics["page_count"] = len(splits)
    except (
        OSError,
        ValueError,
        pymupdf.FileDataError,
        pymupdf.FileNotFoundError,
        PackageNotFoundError,
        BadZipFile,
        XMLSyntaxError,
    ):
        parser.exit(
            1,
            "Error: could not read the document. "
            "Check file permissions and whether the document is valid "
            "and unencrypted.\n",
        )

    with tracer.stage("clean", heartbeat=True) as metrics:
        cleaned_splits = clean_pages(splits)
        metrics["input_pages"] = len(splits)
        metrics["output_pages"] = len(cleaned_splits)

    if not cleaned_splits:
        parser.error("Document contains no extractable text.")

    with tracer.stage("chunk", heartbeat=True) as metrics:
        chunks = chunker.chunk(cleaned_splits)
        metrics["chunk_count"] = len(chunks)
        metrics["short_chunks_under_30_chars"] = sum(
            len(chunk["text"]) < 30 for chunk in chunks
        )

    if not chunks:
        parser.error("No nonempty chunks were generated.")

    print(
        f"Created {len(chunks)} chunks from {len(cleaned_splits)} document sections. "
        "Embeddings run sequentially; chunk timings include SDK retry waits.",
        flush=True,
    )

    # Check database availability before requesting embeddings.
    try:
        with tracer.stage("database_init", heartbeat=True):
            init_db()
    except (psycopg.Error, ValueError):
        parser.exit(
            1,
            "Error: database initialization failed. "
            "Check the connection settings, server, and pgvector setup.\n",
        )

    try:
        with tracer.stage("embedding_setup", heartbeat=True):
            from app.ingestion.embedder import embed_chunks

        with tracer.stage("embedding", chunk_count=len(chunks)):
            embedded_chunks = embed_chunks(chunks, tracer=tracer)
    except APIError as exc:
        parser.exit(
            1,
            f"Gemini request failed: "
            f"HTTP {exc.code}, status={exc.status}.\n",
        )
    except (httpx.HTTPError, OSError):
        parser.exit(
            1,
            "Error: could not communicate with Gemini. "
            "Check your connection and try again.\n",
        )
    except ValueError:
        parser.exit(
            1,
            "Error: embedding configuration or response was invalid. "
            "Check GEMINI_API_KEY and the embedding settings.\n",
        )

    try:
        with tracer.stage("database_save", heartbeat=True, chunk_count=len(embedded_chunks)):
            insert_chunks(embedded_chunks)
    except (psycopg.Error, ValueError):
        parser.exit(
            1,
            "Error: could not store the chunks. "
            "Check the database connection and table schema.\n",
        )

    return len(embedded_chunks)


if __name__ == "__main__":
    main()
