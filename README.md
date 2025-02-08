# BigData Stack

This project integrates a range of big data and analytical technologies into a single, Docker Compose–based environment. The infrastructure is designed to facilitate end-to-end workflows from data ingestion and processing to real-time analytics and machine learning experiment tracking.

## Overview

The project includes the following components:

- **Zookeeper & Kafka:** For real-time data streaming and messaging.
- **Hadoop & Hive:** Distributed storage and SQL-based querying of big data.
- **Spark:** Real-time and batch data processing.
- **Cassandra & MongoDB:** NoSQL databases.
- **MinIO:** An S3-compatible object storage solution for local artifact storage.
- **Airflow:** Workflow orchestration for ETL pipelines.
- **Prometheus & Grafana:** Monitoring and visualization.
- **Elasticsearch & Kibana:** Log aggregation, search, and analytics.
- **MLflow:** Tracking and managing machine learning experiments.
- **RAG Usecase (rag_usecase):** A Python example demonstrating a Retrieval Augmented Generation (RAG) pipeline that combines document retrieval and text generation.
- **Atlas, Ranger, etc.:** Additional services that may be configured as needed.

## Requirements

- **Docker** and **Docker Compose:** To run the containerized services.
- **Git:** For version control.

## Setup and Running the Project

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/bigdata-stack.git
   cd bigdata-stack

    2. Check the .gitignore File:
   Ensure that the repository includes a .gitignore file that ignores unnecessary files (e.g., .DS_Store, env/, .env, MLflow artifact folders, etc.). An example .gitignore file is provided in the repository.
    3. Build and Run the Containers:
   Use Docker Compose to build and start all services:
   ```

docker-compose up --build

This command will start all the components, including Kafka, Hadoop, Hive, Spark, MinIO, MLflow, and the other services.

    4. Verify the Setup:
    • MLflow UI: Open http://localhost:5001 in your browser to view MLflow experiments.
    • MinIO Console: Access MinIO at http://localhost:9001 (default credentials: minioadmin / minioadmin) to view your S3-compatible buckets.
    • Other Services: Check the respective ports for Airflow, Prometheus, Grafana, Kibana, etc.
    5. Running the RAG Usecase:

Navigate to the rag_usecase directory:

cd rag_usecase

Install the required Python dependencies:

pip install -r requirements.txt

Run the RAG use case:

python3 rag_usecase.py

This script will:
• Generate embeddings for sample text and documents.
• Set up a Qdrant collection.
• Retrieve the most relevant document for a given query.
• Generate a response using a text generation model.
• Log parameters, metrics, and artifacts (stored in MinIO via MLflow).

Artifact Storage with MinIO

The MLflow service is configured to use MinIO as its artifact store. In your docker-compose.yml, the MLflow service includes the following environment variables:
• AWS_ACCESS_KEY_ID: minioadmin
• AWS_SECRET_ACCESS_KEY: minioadmin
• MLFLOW_S3_ENDPOINT_URL: <http://minio:9000>
• MLFLOW_ARTIFACT_ROOT: s3://mlflow-artifacts

Make sure that the bucket mlflow-artifacts exists in MinIO. If it does not exist, you can create it using the AWS CLI:

aws s3 mb s3://mlflow-artifacts --endpoint-url <http://localhost:9000> --profile minio

Contributing

Feel free to open issues or pull requests if you have suggestions or improvements.

License

MIT License
