import json
import requests
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StructType, StringType, ArrayType, DoubleType

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

schema = StructType() \
    .add("product_id", StringType()) \
    .add("product_name", StringType()) \
    .add("description", StringType()) \
    .add("timestamp", StringType())

def get_embedding_api(text):
    try:
        url = "http://host.docker.internal:11434/api/embed"
        payload = {"model": "mxbai-embed-large", "input": text}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding") or data.get("embeddings")
            if embedding and isinstance(embedding[0], list):
                embedding = embedding[0]
            return embedding
        else:
            logging.error(f"Error from Ollama API: {response.text}")
            return [0.0] * 1024
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return [0.0] * 1024

embedding_udf = udf(get_embedding_api, ArrayType(DoubleType()))

def main():
    spark = SparkSession.builder \
        .appName("Product_RAG") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4") \
        .config("spark.kafka.bootstrap.servers", "kafka:9092") \
        .getOrCreate()

    # Kafka topic'inden streaming veri okuma
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
        .format("console") \
        .option("truncate", False) \
        .option("numRows", 10) \
        .trigger(processingTime='5 seconds') \
        .start()

    logging.info("Streaming query started...")
    query.awaitTermination()

if __name__ == "__main__":
    main()