import json
import time
from confluent_kafka import Producer
from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key="YOUR_NEWSAPI_KEY")

def fetch_latest_news(query, language="en", page_size=5):
    response = newsapi.get_everything(
        q=query, language=language, page_size=page_size, sort_by="publishedAt"
    )
    articles = response.get("articles", [])

    formatted_articles = [
        {
            "id": f"article_{i}",
            "title": article["title"],
            "content": article["description"] or "No description available",
            "source": article["source"]["name"],
            "published_at": article["publishedAt"],
            "url": article["url"],
        }
        for i, article in enumerate(articles)
    ]
    return formatted_articles


def kafka_producer(broker, topic, query):
    producer = Producer({"bootstrap.servers": broker})

    try:
        while True:
            articles = fetch_latest_news(query=query)
            for article in articles:
                producer.produce(topic, value=json.dumps(article))
                print(f"Produced: {article['title']} from {article['source']}")

            producer.flush()
            time.sleep(10) 
    except KeyboardInterrupt:
        print("Stopping producer...")


if __name__ == "__main__":
    kafka_producer(broker="localhost:9092", topic="news", query="technology")
