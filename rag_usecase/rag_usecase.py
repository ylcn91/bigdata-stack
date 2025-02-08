import requests
import mlflow
import logging
import json
import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

# Configure logging to output INFO-level messages with timestamps.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# --- Ollama API Functions ---

def get_embedding(text: str, model: str = "mxbai-embed-large") -> list:
    """
    Generate an embedding for the given text using Ollama's embed endpoint.
    If the returned embedding is a nested list (e.g. [[...]]), extract the inner list.
    """
    logging.info("Generating embedding for text: %s", text)
    url = "http://localhost:11434/api/embed"
    payload = {"model": model, "input": text}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        # The API may return the embedding under "embedding" or "embeddings".
        embedding = data.get("embedding") or data.get("embeddings")
        if isinstance(embedding, list):
            # If it's a nested list, extract the inner list.
            if embedding and isinstance(embedding[0], list):
                embedding = embedding[0]
            logging.info("Embedding generated with dimension: %d", len(embedding))
            return embedding
        else:
            raise ValueError("Unexpected embedding format: " + str(embedding))
    else:
        raise Exception(f"get_embedding error: {response.text}")


def generate_response(prompt: str, model: str = "phi3:latest") -> str:
    """
    Generate a response for the given prompt using Ollama's generate endpoint.
    This function processes a streaming response that may contain multiple JSON objects
    separated by newline characters. It accumulates the 'response' field until the 
    'done' flag is True.
    """
    logging.info("Generating response for prompt: %s", prompt)
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt}
    response = requests.post(url, json=payload, stream=True)
    full_response = ""
    done = False
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            data = json.loads(line)
            part = data.get("response", "")
            full_response += part
            done = data.get("done", False)
            logging.info("Received chunk: %s | done: %s", part, done)
            if done:
                break
        except json.JSONDecodeError as e:
            logging.error("JSON decode error for line: %s", line)
            continue
    logging.info("Full response generated: %s", full_response)
    return full_response


# --- Qdrant Operations ---

def setup_qdrant_collection(client: QdrantClient, collection_name: str, vector_size: int):
    """
    Prepare a Qdrant collection with the specified vector dimension.
    If the collection exists, delete it first to ensure that the dimension is set correctly.
    """
    logging.info("Setting up Qdrant collection '%s' with vector dimension %d", collection_name, vector_size)
    collections = client.get_collections().collections
    if any(col.name == collection_name for col in collections):
        logging.info("Collection '%s' exists, deleting it.", collection_name)
        client.delete_collection(collection_name)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    logging.info("Collection '%s' created successfully.", collection_name)


def add_documents_to_qdrant(client: QdrantClient, collection_name: str, documents: list):
    """
    For each document, generate an embedding and add it to the Qdrant collection.
    """
    logging.info("Adding %d documents to Qdrant collection '%s'.", len(documents), collection_name)
    points = []
    for idx, doc in enumerate(documents):
        logging.info("Processing document %d: %s", idx, doc)
        embedding = get_embedding(doc)
        points.append({"id": idx, "vector": embedding, "payload": {"text": doc}})
    client.upsert(collection_name=collection_name, points=points)
    logging.info("Documents added successfully.")


def search_qdrant(client: QdrantClient, collection_name: str, query_vector: list, limit: int = 1):
    """
    Search the Qdrant collection for the document(s) most similar to the query vector.
    """
    logging.info("Searching Qdrant collection '%s' using the query vector.", collection_name)
    results = client.search(
        collection_name=collection_name, query_vector=query_vector, limit=limit
    )
    logging.info("Search results: %s", results)
    return results


# --- Main Workflow ---

def main():
    logging.info("Starting RAG Use Case Script")

    # Set up MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5001")
    mlflow.set_experiment("RAG_UseCase_Example")
    logging.info("MLflow experiment set to 'RAG_UseCase_Example'.")

    # Sample documents (facts about llamas)
    documents = [
        "Llamas are members of the camelid family meaning they're pretty closely related to vicuñas and camels.",
        "Llamas were first domesticated and used as pack animals 4,000 to 5,000 years ago in the Peruvian highlands.",
        "Llamas can grow as much as 6 feet tall though the average llama is between 5 feet 6 inches and 5 feet 9 inches tall.",
        "Llamas weigh between 280 and 450 pounds and can carry 25 to 30 percent of their body weight.",
        "Llamas are vegetarians and have very efficient digestive systems.",
        "Llamas live to be about 20 years old, though some only live for 15 years and others live to be 30 years old.",
    ]

    # Connect to Qdrant (ensure your Qdrant container is running on localhost:6333)
    logging.info("Connecting to Qdrant at localhost:6333")
    qdrant_client = QdrantClient(host="localhost", port=6333)
    collection_name = "llama_docs"

    # Determine the embedding vector size using a sample text
    sample_text = "Sample text to determine embedding dimension."
    sample_embedding = get_embedding(sample_text)
    vector_size = len(sample_embedding)
    logging.info("Determined embedding vector size: %d", vector_size)

    # Set up the Qdrant collection with the correct vector dimension
    setup_qdrant_collection(qdrant_client, collection_name, vector_size)

    # Add documents to Qdrant
    add_documents_to_qdrant(qdrant_client, collection_name, documents)

    # Process a user query
    query_text = "What animals are llamas related to?"
    query_embedding = get_embedding(query_text)

    # Search Qdrant for the nearest document
    search_results = search_qdrant(qdrant_client, collection_name, query_embedding, limit=1)
    if search_results and len(search_results) > 0:
        retrieved_doc = search_results[0].payload.get("text", "")
        similarity_score = search_results[0].score
        logging.info("Retrieved document: %s with similarity score: %s", retrieved_doc, similarity_score)
    else:
        retrieved_doc = ""
        similarity_score = None
        logging.warning("No search results found.")

    # Build the generation prompt
    generation_prompt = f"Using this data: {retrieved_doc}. Respond to this prompt: {query_text}"
    logging.info("Generation prompt: %s", generation_prompt)

    # Generate the final response using the generation endpoint
    final_response = generate_response(generation_prompt, model="phi3:latest")

    # Truncate the final response to 500 characters (the MLflow parameter limit)
    truncated_final_response = final_response[:500]
    
    # Log the experiment details in MLflow.
    # Also, log the full response as an artifact.
    with mlflow.start_run():
        mlflow.log_param("embedding_model", "mxbai-embed-large")
        mlflow.log_param("generation_model", "phi3:latest")
        mlflow.log_param("query_text", query_text)
        mlflow.log_param("retrieved_document", retrieved_doc)
        mlflow.log_param("generation_prompt", generation_prompt)
        mlflow.log_metric("similarity_score", similarity_score if similarity_score is not None else -1)
        mlflow.log_param("final_response", truncated_final_response)
        
        artifact_path = "final_response.txt"
        with open(artifact_path, "w") as f:
            f.write(final_response)
        mlflow.log_artifact(artifact_path)
        logging.info("Experiment logged in MLflow.")

    # Print final outputs
    print("Query:", query_text)
    print("Retrieved Document:", retrieved_doc)
    print("Generation Prompt:", generation_prompt)
    print("Final Response:", final_response)
    logging.info("Script completed successfully.")


if __name__ == "__main__":
    main()