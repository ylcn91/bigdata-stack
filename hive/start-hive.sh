#!/bin/bash

nohup hive --service metastore &
sleep 5
nohup hive --service hiveserver2 &

sleep 5

tail -f /opt/hive/logs/*