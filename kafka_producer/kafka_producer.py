import json
import time
import logging
import argparse
from confluent_kafka import Producer
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def check_kafka_connection(producer, topic):
   try:
       metadata = producer.list_topics(timeout=10)
       if topic not in metadata.topics:
           logging.warning(f"Topic '{topic}' not found. Will be auto-created.")
       return True
   except Exception as e:
       logging.error(f"Failed to connect to Kafka: {e}")
       return False

def produce_messages(broker: str, topic: str):
   producer_config = {
       'bootstrap.servers': broker,
       'socket.timeout.ms': 10000,
       'message.timeout.ms': 10000,
       'request.timeout.ms': 10000,
       'metadata.request.timeout.ms': 10000,
       'client.id': 'products-producer'
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
           logging.error(f'Message delivery failed: {err}')
           messages_failed += 1
       else:
           logging.info(f'Message delivered to: {msg.topic()} [{msg.partition()}]')
           messages_sent += 1
   
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

   try:
       for product in sample_products:
           product['timestamp'] = datetime.now().isoformat()
           product_json = json.dumps(product).encode('utf-8')
           
           producer.produce(topic, value=product_json, callback=delivery_callback)
           producer.poll(0)
           
           logging.info(f"Message queued: {product['product_id']}")
           time.sleep(1)

       logging.info("All messages queued, waiting for delivery completion...")
       producer.flush(timeout=10)
       
   except Exception as e:
       logging.error(f"Error occurred: {e}")
   finally:
       logging.info(f"Process completed. Messages sent: {messages_sent}, Failed: {messages_failed}")

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Kafka Product Producer")
   parser.add_argument("--broker", type=str, default="localhost:9092")
   parser.add_argument("--topic", type=str, default="products")
   
   args = parser.parse_args()
   produce_messages(args.broker, args.topic)