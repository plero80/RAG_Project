import os

import psycopg
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg import register_vector


load_dotenv()


POSTGRES_URL = os.getenv("POSTGRES_URL")


def get_connection():
    if POSTGRES_URL is None:
        raise ValueError("POSTGRES_URL is not defined")

    return psycopg.connect(POSTGRES_URL)


def init_db():
    with get_connection() as conn:

        # Enable pgvector inside PostgreSQL
        conn.execute(
            "CREATE EXTENSION IF NOT EXISTS vector"
        )

        # Tell psycopg how PostgreSQL vectors should
        # become Python objects and vice versa.
        register_vector(conn)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id BIGSERIAL PRIMARY KEY,
                chunk_id UUID NOT NULL UNIQUE,
                document_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                page_number INTEGER,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                split_strategy TEXT NOT NULL,
                embedding VECTOR(768) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        
        
def insert_chunks(chunks: list[dict]) -> None:

    with get_connection() as conn:

        register_vector(conn)

        for chunk in chunks:

            vector = Vector(
                chunk["embedding"]
            )

            conn.execute(
                """
                INSERT INTO chunks (
                    chunk_id,
                    document_id,
                    filename,
                    page_number,
                    chunk_index,
                    chunk_text,
                    split_strategy,
                    embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

                ON CONFLICT (chunk_id)
                DO UPDATE SET
                    document_id = EXCLUDED.document_id,
                    filename = EXCLUDED.filename,
                    page_number = EXCLUDED.page_number,
                    chunk_index = EXCLUDED.chunk_index,
                    chunk_text = EXCLUDED.chunk_text,
                    split_strategy = EXCLUDED.split_strategy,
                    embedding = EXCLUDED.embedding
                """,
                (                
                    chunk["chunk_id"],
                    chunk["document_id"],
                    chunk["document_name"],
                    chunk.get("page_number"),
                    chunk["chunk_index"],
                    chunk["text"],
                    chunk["strategy"],
                    vector,                   
                )
            )

        conn.commit()
        
        
def search_similar(
    query_embedding: list[float],
    limit: int = 5,
    split_strategy: str | None = None
) -> list[dict]:
    
    
    with get_connection() as conn:
        
        register_vector(conn)
        
        query_vector = Vector(query_embedding)
        
        
        if split_strategy is None:
            rows = conn.execute(
                """
                SELECT
                    filename AS document,
                    page_number AS page,
                    chunk_id,
                    chunk_text AS text,
                    1 - (embedding <=> %s) AS similarity,
                    split_strategy AS strategy

                FROM chunks

                ORDER BY embedding <=> %s

                LIMIT %s
                """,
                (
                    query_vector,
                    query_vector,
                    limit
                )
            ).fetchall()
        
        else: 
            rows = conn.execute(
                """
                SELECT
                    filename AS document,
                    page_number AS page,
                    chunk_id,
                    chunk_text AS text,
                    1 - (embedding <=> %s) AS similarity,
                    split_strategy AS strategy

                FROM chunks
                
                WHERE split_strategy = %s

                ORDER BY embedding <=> %s

                LIMIT %s
                """,
                (
                    query_vector,
                    split_strategy,
                    query_vector,
                    limit
                )
            ).fetchall()
        
        
            
        results = []
        for row in rows:

            results.append({
                "document": row[0],
                "page": row[1],
                "chunk_id": str(row[2]),
                "text": row[3],
                "similarity": row[4],
                "strategy": row[5]
            })

        return results