import os

import psycopg
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg import register_vector


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if DATABASE_URL is None:
        raise ValueError("DATABASE_URL is not defined")

    return psycopg.connect(DATABASE_URL)


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

                document TEXT NOT NULL,

                page INTEGER NOT NULL,

                chunk_id INTEGER NOT NULL,

                text TEXT NOT NULL,

                embedding VECTOR(768) NOT NULL,

                UNIQUE(document, chunk_id)
            )
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
                    document,
                    page,
                    chunk_id,
                    text,
                    embedding
                )
                VALUES (%s, %s, %s, %s, %s)

                ON CONFLICT (document, chunk_id)
                DO UPDATE SET
                    page = EXCLUDED.page,
                    text = EXCLUDED.text,
                    embedding = EXCLUDED.embedding
                """,
                (
                    chunk["document"],
                    chunk["page"],
                    chunk["chunk_id"],
                    chunk["text"],
                    vector
                )
            )

        conn.commit()
        
        
def search_similar(
    query_embedding: list[float],
    limit: int = 5
) -> list[dict]:
    
    
    with get_connection() as conn:
        
        register_vector(conn)
        
        query_vector = Vector(query_embedding)
        
        rows = conn.execute(
            """
            SELECT
                document,
                page,
                chunk_id,
                text,

                1 - (embedding <=> %s)
                    AS similarity

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
        
        
        results = []
        for row in rows:

            results.append({
                "document": row[0],
                "page": row[1],
                "chunk_id": row[2],
                "text": row[3],
                "similarity": row[4]
            })

        return results