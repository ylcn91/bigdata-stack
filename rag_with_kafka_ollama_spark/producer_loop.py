import json
import time
import logging
import argparse
import random
import string
from datetime import datetime
from confluent_kafka import Producer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def check_kafka_connection(producer, topic):
    """
    Checks the Kafka connection and verifies if the topic exists.
    Logs a warning if the topic is not found (it will be auto-created).
    """
    try:
        metadata = producer.list_topics(timeout=10)
        if topic not in metadata.topics:
            logging.warning(f"Topic '{topic}' not found. It will be auto-created.")
        return True
    except Exception as e:
        logging.error(f"Kafka connection failed: {e}")
        return False

def generate_random_product():
    """
    Generates a random product with a random product_id, product_name,
    description, and current timestamp.
    """
    product_id = "P" + ''.join(random.choices(string.digits, k=3))  # e.g., P123
    product_names = [
        "Industrial Automation Controller",
        "Smart Sensor",
        "Robotic Arm",
        "Automated Conveyor Belt",
        "Industrial IoT Gateway"
    ]
    product_name = random.choice(product_names)
    descriptions = {
        "Industrial Automation Controller": "A programmable logic controller (PLC) designed for industrial automation applications.",
        "Smart Sensor": "A wireless sensor that monitors temperature, pressure, and humidity in industrial settings.",
        "Robotic Arm": "An advanced robotic arm used for precise assembly operations in manufacturing.",
        "Automated Conveyor Belt": "A conveyor belt system integrated with sensors and controls for automated material handling.",
        "Industrial IoT Gateway": "A gateway device that aggregates data from various industrial sensors and transmits it to the cloud."
    }
    description = descriptions[product_name]
    timestamp = datetime.now().isoformat()
    return {
        "product_id": product_id,
        "product_name": product_name,
        "description": description,
        "timestamp": timestamp
    }

def produce_messages(broker: str, topic: str, interval: float = 1.0):
    """
    Continuously produces messages to Kafka by dynamically generating product data.
    """
    producer_config = {
        'bootstrap.servers': broker,
        'socket.timeout.ms': 10000,
        'message.timeout.ms': 10000,
        'request.timeout.ms': 10000,
        'metadata.request.timeout.ms': 10000,
        'client.id': 'dynamic-products-producer'
    }
    producer = Producer(producer_config)

    # Check Kafka connection
    if not check_kafka_connection(producer, topic):
        logging.error("Kafka connection failed. Terminating program.")
        return

    messages_sent = 0
    messages_failed = 0

    def delivery_callback(err, msg):
        nonlocal messages_sent, messages_failed
        if err:
            logging.error(f"Message delivery failed: {err}")
            messages_failed += 1
        else:
            logging.info(f"Message delivered to: {msg.topic()} [{msg.partition()}]")
            messages_sent += 1

    try:
        while True:
            product = generate_random_product()
            product_json = json.dumps(product).encode('utf-8')
            producer.produce(topic, value=product_json, callback=delivery_callback)
            producer.poll(0)
            logging.info(f"Message queued: {product['product_id']}")
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Waiting for message deliveries...")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    finally:
        producer.flush(timeout=10)
        logging.info(f"Process completed. Messages sent: {messages_sent}, Failed: {messages_failed}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dynamic Kafka Product Producer")
    parser.add_argument("--broker", type=str, default="localhost:9092", help="Kafka broker address (default: localhost:9092)")
    parser.add_argument("--topic", type=str, default="products", help="Kafka topic name (default: products)")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval between messages in seconds (default: 1.0)")
    args = parser.parse_args()

    produce_messages(args.broker, args.topic, args.interval)