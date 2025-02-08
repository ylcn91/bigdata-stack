import json
import requests
import logging
import uuid
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StructType, StringType, ArrayType, DoubleType

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

schema = StructType() \
    .add("product_id", StringType()) \
    .add("product_name", StringType()) \
    .add("description", StringType()) \
    .add("timestamp", StringType())

def get_embedding_api(text):
    try:
        url = "http://host.docker.internal:11434/api/embed"
        payload = {
            "model": "mxbai-embed-large",
            "prompt": text
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding")
            if embedding:
                return embedding
            return [0.0] * 1024
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return [0.0] * 1024

embedding_udf = udf(get_embedding_api, ArrayType(DoubleType()))

def write_to_qdrant(batch_df, batch_id):
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import VectorParams, Distance

    client = QdrantClient(host="host.docker.internal", port=6333)

    try:
        client.get_collection("products_collection")
    except Exception:
        logging.info("Creating Qdrant collection: products_collection")
        client.recreate_collection(
            collection_name="products_collection",
            vectors_config={
                "default": VectorParams(size=1024, distance=Distance.COSINE)
            }
        )

    records = batch_df.collect()
    points = []
    for row in records:
        product = row.asDict()
        valid_point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, product["product_id"]))
        points.append({
            "id": valid_point_id,
            "vector": {
                "default": product["embedding"]
            },
            "payload": {
                "product_name": product["product_name"],
                "description": product["description"],
                "timestamp": product["timestamp"]
            }
        })

    if points:
        client.upsert(
            collection_name="products_collection",
            points=points
        )
        logging.info(f"Upserted {len(points)} points to Qdrant.")

def main():
    spark = SparkSession.builder \
        .appName("Product_RAG") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4") \
        .config("spark.kafka.bootstrap.servers", "kafka:9092") \
        .getOrCreate()
    
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "products") \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", 10) \
        .load()
    
    df = kafka_df.selectExpr("CAST(value AS STRING) as json_str")
    df = df.select(from_json(col("json_str"), schema).alias("data")).select("data.*")
    
    df_with_embeddings = df.withColumn("embedding", embedding_udf(col("description")))
    
    query = df_with_embeddings.writeStream \
        .outputMode("append") \
        .foreachBatch(write_to_qdrant) \
        .start()
    
    logging.info("Spark Streaming job started and writing embeddings to Qdrant...")
    query.awaitTermination()

if __name__ == "__main__":
    main()