import json
import requests
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StructType, StringType, ArrayType, DoubleType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Kafka mesajları için şema tanımlama (JSON formatında 'product_id', 'product_name', 'description' ve 'timestamp' alanları)
schema = StructType() \
    .add("product_id", StringType()) \
    .add("product_name", StringType()) \
    .add("description", StringType()) \
    .add("timestamp", StringType())

# Embedding API'sini çağıran fonksiyon (Ollama endpoint'i kullanarak)
def get_embedding_api(text):
    try:
        url = "http://localhost:11434/api/embed"
        payload = {"model": "mxbai-embed-large", "input": text}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding") or data.get("embeddings")
            if embedding and isinstance(embedding[0], list):
                embedding = embedding[0]
            return embedding
        else:
            return [0.0] * 1024
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return [0.0] * 1024

# Embedding için UDF kaydı
embedding_udf = udf(get_embedding_api, ArrayType(DoubleType()))

def main():
    # Spark oturumu oluşturma
    spark = SparkSession.builder \
        .appName("Product_RAG") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4") \
        .getOrCreate()

    # Kafka topic'inden streaming veri okuma
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "products") \
        .load()

    # Binary 'value' kolonunu string'e çevirme ve JSON parse etme
    df = kafka_df.selectExpr("CAST(value AS STRING) as json_str")
    df = df.select(from_json(col("json_str"), schema).alias("data")).select("data.*")

    # Ürün açıklamaları için embedding oluşturma
    df_with_embeddings = df.withColumn("embedding", embedding_udf(col("description")))

    # Konsola yazdırma (demo amaçlı)
    query = df_with_embeddings.writeStream \
        .outputMode("append") \
        .format("console") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
