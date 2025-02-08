#!/bin/bash

# Initialize metastore schema
echo "Initializing Hive Metastore schema..."
schematool -initSchema -dbType derby

# Start metastore
echo "Starting Hive Metastore..."
hive --service metastore &
sleep 10

# Start HiveServer2
echo "Starting HiveServer2..."
hiveserver2 &
sleep 5

echo "Hive Metastore and HiveServer2 started"

# Keep container running
tail -f /dev/null