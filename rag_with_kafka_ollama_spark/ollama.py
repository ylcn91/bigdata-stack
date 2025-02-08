import logging
import argparse
import requests
from qdrant_client import QdrantClient

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")


def get_embedding_api(text):
    """
    Calls the Ollama embedding API to generate an embedding vector.
    Ollama expects the key "input" for the text.
    Checks for either "embedding" or "embeddings" in the response.
    Falls back to a 1024-dimensional zero vector if nothing valid is returned.
    """
    url = "http://localhost:11434/api/embed"
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

        # If the embedding is nested (i.e. a list within a list), flatten it.
        if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], list):
            embeddings = embeddings[0]
        return embeddings
    except Exception as e:
        logging.error("Error calling embedding API: %s", e)
        return [0.0] * 1024


def search_products(query_text, limit=5):
    """
    Searches the Qdrant collection 'products_collection' using the embedding
    of the provided query text.

    Returns the search results (List[ScoredPoint]) from Qdrant.
    """
    client = QdrantClient(host="localhost", port=6333)
    query_vector = get_embedding_api(query_text)
    if not query_vector:
        raise ValueError("No valid embedding returned; cannot perform search.")

    if isinstance(query_vector, list) and query_vector and isinstance(query_vector[0], list):
        query_vector = query_vector[0]

    results = client.search(
        collection_name="products_collection",
        query_vector=("default", query_vector),
        limit=limit,
        with_payload=True
    )

    return results


def generate_response(query, retrieved_data):
    """
    Calls the Ollama generate API to produce a natural language answer.
    The prompt combines the retrieved product data and the original query.
    """
    import json

    url = "http://localhost:11434/api/generate"
    prompt = f"Using this data: {retrieved_data}. Respond to this prompt: {query}"
    payload = {
        "model": "phi3:latest",
        "prompt": prompt
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.debug("Raw generation API response: %s", response.text)

        full_response_parts = []
        for line in response.text.splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except Exception as ex:
                logging.error("Error parsing line: %s", ex)
                continue
            full_response_parts.append(data.get("response", ""))
            if data.get("done", False):
                break

        final_text = "".join(full_response_parts)
        logging.debug("Combined generation API response: %s", final_text)
        return final_text if final_text else "No response generated."
    except Exception as e:
        logging.error("Error calling generation API: %s", e)
        return "Error generating response."


def main():
    parser = argparse.ArgumentParser(
        description="Semantic Search with Retrieval-Augmented Generation using Ollama and Qdrant."
    )
    parser.add_argument("--query", type=str, default="Industrial automation",
                        help="Search query text (default: 'Industrial automation').")
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of search results to return (default: 5).")
    parser.add_argument("--augment", action="store_true",
                        help="Use this flag to include the generation step for a final answer.")
    args = parser.parse_args()

    try:
        results = search_products(args.query, args.limit)
        if not results:
            logging.info("No results found for the given query.")
            return

        retrieved_info = ""
        print(f"\nSearch results for query: '{args.query}'")
        print("-" * 50)
        for hit in results:
            score = getattr(hit, 'score', "N/A")
            payload = getattr(hit, 'payload', {}) or {}
            product_name = payload.get('product_name', 'N/A')
            description = payload.get('description', 'N/A')
            timestamp = payload.get('timestamp', 'N/A')
            result_str = (
                f"Score: {score}, "
                f"Product: {product_name}, "
                f"Description: {description}, "
                f"Timestamp: {timestamp}"
            )
            print(result_str)
            retrieved_info += result_str + "\n"

        if args.augment:
            final_answer = generate_response(args.query, retrieved_info)
            print("\nFinal Augmented Response:")
            print("-" * 50)
            print(final_answer)

    except Exception as e:
        logging.error("Error during search and generation: %s", e)


if __name__ == "__main__":
    main()