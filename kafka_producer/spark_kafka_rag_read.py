import logging
import requests
import argparse
from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchRequest

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")


def get_embedding_api(text):
    """
    Calls the Ollama embedding API to generate an embedding vector.

    Ollama expects the key "input" for the text.
    Checks for either "embedding" or "embeddings" in the response.
    Falls back to a 1024-dimensional zero vector if nothing valid is returned.
    """
    url = "http://host.docker.internal:11434/api/embed"
    payload = {
        "model": "mxbai-embed-large",
        "input": text
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        logging.debug("Embedding API response: %s", data)

        embeddings = data.get("embedding") or data.get("embeddings")
        if not embeddings:
            logging.warning("No embeddings returned by API, using fallback zero vector.")
            return [0.0] * 1024
        return embeddings
    except Exception as e:
        logging.error("Error calling embedding API: %s", e)
        return [0.0] * 1024


def search_products(query_text, limit=5):
    """
    Searches the Qdrant vector collection 'products_collection' using the embedding
    of the provided query_text.

    Returns the search results from Qdrant.
    """
    # Connect to Qdrant.
    client = QdrantClient(host="host.docker.internal", port=6333)

    # Get the embedding vector for the query.
    query_vector = get_embedding_api(query_text)
    if not query_vector:
        raise ValueError("No valid embedding returned; cannot perform search.")

    # If the embedding is returned as a nested list, flatten it:
    if isinstance(query_vector, list) and query_vector and isinstance(query_vector[0], list):
        query_vector = query_vector[0]

    # Build a SearchRequest with a flat list of floats.
    search_request = SearchRequest(
        vector=query_vector,
        limit=limit
    )

    # Call query_points using the SearchRequest object.
    search_result = client.query_points(
        collection_name="products_collection",
        query=search_request
    )

    return search_result


def main():
    # Set up command-line arguments.
    parser = argparse.ArgumentParser(
        description="Verify vectors in Qdrant by performing a search query using Ollama embeddings."
    )
    parser.add_argument("--query", type=str, default="Industrial automation",
                        help="Search query text (default: 'Industrial automation').")
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of search results to return (default: 5).")
    args = parser.parse_args()

    try:
        results = search_products(args.query, args.limit)
        if not results:
            logging.info("No results found for the given query.")
            return

        print(f"\nSearch results for query: '{args.query}'")
        print("-" * 50)
        for hit in results:
            # Each hit should have a 'score' and a 'payload' containing product info.
            score = hit.score if hasattr(hit, 'score') else "N/A"
            payload = hit.payload if hasattr(hit, 'payload') else {}
            product_name = payload.get('product_name', 'N/A')
            description = payload.get('description', 'N/A')
            timestamp = payload.get('timestamp', 'N/A')

            print(f"Score      : {score}")
            print(f"Product    : {product_name}")
            print(f"Description: {description}")
            print(f"Timestamp  : {timestamp}")
            print("-" * 50)
    except Exception as e:
        logging.error("Error during search: %s", e)


if __name__ == "__main__":
    main()