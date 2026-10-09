import time

from app.ingestion.embedder import embed_query
from app.db.database import search_similar
from app.core.tracer import (
    create_trace_id,
    trace
)



def search(
    question: str,
    limit: int = 5,
    split_strategy: str | None = None
)  -> list[dict] :
     
    
    # 1.) Create tracer id
    tracer_id = create_trace_id()
    start = time.perf_counter()
    
    # 2.) embed the question
    embedded_question = embed_query(question)
    
    embedding_ms = (
        time.perf_counter() - start
    ) * 1000
    
    trace(
        tracer_id,
        "embedding query",
        {
            "dimension": len(embedded_question),
            "latency_ms": embedding_ms
        }
    )
    
    
    # 3.) Find k similar chunks.
    start = time.perf_counter()
    
    results = search_similar(embedded_question, limit, split_strategy)
    
    retrieval_ms = (
        time.perf_counter() - start
    ) * 1000
    
    
    # 4.) Trace the data
    trace(
        tracer_id,
        "retriever",
        {
            "results": [
                {
                    "document": result[
                        "document"
                    ],
                    "page": result[
                        "page"
                    ],
                    "chunk_id": result[
                        "chunk_id"
                    ],
                    "similarity": float(
                        result["similarity"]
                    )
                }
                for result in results
            ]
        }
    )
    
    
    return results