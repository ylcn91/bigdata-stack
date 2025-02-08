# hive/Dockerfile
FROM bde2020/hive:2.3.2-postgresql-metastore

COPY hive-site.xml /opt/hive/conf/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 10000 10002 9083

ENTRYPOINT ["/entrypoint.sh"]