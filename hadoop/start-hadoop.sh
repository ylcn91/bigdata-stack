#!/bin/bash

service ssh start

echo "127.0.0.1 hadoop" >> /etc/hosts

chown -R root:root $HADOOP_HOME
chown -R root:root /hadoop

rm -rf /tmp/hadoop-root/* /hadoop/dfs/name/* /hadoop/dfs/data/*
$HADOOP_HOME/bin/hdfs namenode -format -force

# Environment variables
echo "export JAVA_HOME=/usr/local/openjdk-8" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
echo "export HDFS_NAMENODE_USER=root" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
echo "export HDFS_DATANODE_USER=root" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
echo "export HDFS_SECONDARYNAMENODE_USER=root" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
echo "export YARN_RESOURCEMANAGER_USER=root" >> $HADOOP_HOME/etc/hadoop/yarn-env.sh
echo "export YARN_NODEMANAGER_USER=root" >> $HADOOP_HOME/etc/hadoop/yarn-env.sh

$HADOOP_HOME/sbin/start-dfs.sh
$HADOOP_HOME/sbin/start-yarn.sh

echo "Hadoop servisleri başlatılıyor..."
sleep 10

jps

echo "HDFS sağlık kontrolü yapılıyor..."
hdfs dfsadmin -report

tail -f $HADOOP_HOME/logs/*