FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

RUN pip install mlflow==2.2.2 psycopg2-binary boto3 scikit-learn