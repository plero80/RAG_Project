import argparse
from docx.opc.exceptions import PackageNotFoundError
from google.genai.errors import APIError
import httpx
import psycopg


def main():
    
    
    # CLI 
    parser = argparse.ArgumentParser(description="Process PDF documents")
    parser.add_argument("--query", type=str, required=True, help="Query to find related documents")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--split-strategy",
        type=str,
        choices=["fixed", "sentence", "paragraph"],
        default=None,
        help="Filter by chunking strategy; omit to search all strategies.",
    )

    args = parser.parse_args()
    
    if args.split_strategy is None:
        print(
            "Searching all strategies. "
            "Results may contain overlapping passages."
        )
        
              
    query = args.query.strip()

    if not query:
        parser.error("Query cannot be empty.")

    if args.limit <= 0:
        parser.error("Limit must be greater than zero.")
    
    try :
        from app.rag.retriever import search
        
        results = search(query, args.limit, args.split_strategy)
        if not results:
            print("No results found.")
            return

        for number, result in enumerate(results, start=1):
            page = result["page"]
            page_label = page if page is not None else "N/A"

            print(f"\nResult {number}")
            print(f"Document: {result['document']}")
            print(f"Page: {page_label}")
            print(f"Similarity: {result['similarity']:.4f}")
            print(f"Strategy: {result['strategy']}")
            print(result["text"])
            
    except APIError:
            parser.exit(
                1,
                "Error: Gemini rejected the embedding request. "
                "Check API credentials, quota, and model availability.\n",
            )
    except (httpx.HTTPError):
        parser.exit(
            1,
            "Error: could not communicate with Gemini. "
            "Check your connection and try again.\n",
        )
    except ValueError:
        parser.exit(
            1,
            "Error: invalid configuration or embedding response. "
            "Check GEMINI_API_KEY, POSTGRES_URL, and embedding settings.\n"
        )
    except psycopg.Error:
        parser.exit(
            1,
            "Error: database search failed. "
            "Check POSTGRES_URL, the database server, and table schema.\n",
        )
    except OSError:
        parser.exit(
            1,
            "Error: could not access a required file or write trace logs.\n",
        )
    
    

if __name__ == "__main__":
    main()
    