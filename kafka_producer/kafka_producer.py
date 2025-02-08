import json
import time
import logging
import argparse
from confluent_kafka import Producer
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

def produce_messages(broker: str, topic: str):
    """
    Produce sample product messages to the given Kafka topic.
    """
    # Create a Producer with JSON serialization
    producer = Producer({'bootstrap.servers': broker})
    
    # Sample product data
    sample_products = [
        {
            "product_id": "P001",
            "product_name": "Industrial Automation Controller",
            "description": "A programmable logic controller (PLC) designed for industrial automation applications.",
            "timestamp": datetime.now().isoformat()
        },
        {
            "product_id": "P002",
            "product_name": "Smart Sensor",
            "description": "A wireless sensor that monitors temperature, pressure, and humidity in industrial settings.",
            "timestamp": datetime.now().isoformat()
        },
        {
            "product_id": "P003",
            "product_name": "Robotic Arm",
            "description": "An advanced robotic arm used for precise assembly operations in manufacturing.",
            "timestamp": datetime.now().isoformat()
        },
        {
            "product_id": "P004",
            "product_name": "Automated Conveyor Belt",
            "description": "A conveyor belt system integrated with sensors and controls for automated material handling.",
            "timestamp": datetime.now().isoformat()
        },
        {
            "product_id": "P005",
            "product_name": "Industrial IoT Gateway",
            "description": "A gateway device that aggregates data from various industrial sensors and transmits it to the cloud.",
            "timestamp": datetime.now().isoformat()
        },
    ]
    
    # Delivery callback function
    def delivery_callback(err, msg):
        if err:
            logging.error(f'Failed to deliver message: {err}')
        else:
            logging.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    # Send each product as a message to Kafka
    for product in sample_products:
        try:
            # Update timestamp for each message just before sending
            product['timestamp'] = datetime.now().isoformat()
            
            # Convert product to JSON and encode as UTF-8
            product_json = json.dumps(product).encode('utf-8')
            
            # Produce message
            producer.produce(
                topic=topic,
                value=product_json,
                callback=delivery_callback
            )
            logging.info(f"Sent product: {product}")
            
            # Flush message buffer after each message
            producer.poll(0)
            
            # Add delay to simulate streaming
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error sending message: {e}")
    
    # Flush any remaining messages
    producer.flush()
    logging.info("All messages sent successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Kafka Producer for Products RAG Use Case"
    )
    parser.add_argument(
        "--broker",
        type=str,
        default="localhost:9092",
        help="Kafka broker address (default: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="products",
        help="Kafka topic to produce messages to (default: products)",
    )
    
    args = parser.parse_args()
    produce_messages(args.broker, args.topic)