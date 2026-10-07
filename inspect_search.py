from app.ingestion.embedder import embed_query
from app.db.database import search_similar


question = "What company is this report about?"


query_embedding = embed_query(
    question
)


results = search_similar(
    query_embedding,
    limit=3
)


print(f"\nQUESTION:")
print(question)


for i, result in enumerate(
    results,
    start=1
):

    print(
        f"\n========== RESULT {i} =========="
    )

    print(
        f"Similarity: "
        f"{result['similarity']:.4f}"
    )

    print(
        f"Document: "
        f"{result['document']}"
    )

    print(
        f"Page: "
        f"{result['page']}"
    )

    print()

    print(
        result["text"][:1000]
    )