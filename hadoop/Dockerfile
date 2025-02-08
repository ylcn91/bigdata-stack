FROM openjdk:8-jdk-slim

ENV HADOOP_VERSION=3.3.6
ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    net-tools \
    netcat \
    gnupg \
    openssh-server \
    openssh-client \
    libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 0600 ~/.ssh/authorized_keys

RUN wget https://downloads.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz && \
    tar -xzf hadoop-${HADOOP_VERSION}.tar.gz && \
    mv hadoop-${HADOOP_VERSION} ${HADOOP_HOME} && \
    rm hadoop-${HADOOP_VERSION}.tar.gz

COPY config/* $HADOOP_CONF_DIR/

RUN mkdir -p /hadoop/dfs/name && \
    mkdir -p /hadoop/dfs/data && \
    chmod -R 777 /hadoop

RUN mkdir -p /run/sshd

WORKDIR $HADOOP_HOME

COPY start-hadoop.sh /start-hadoop.sh
RUN chmod +x /start-hadoop.sh

EXPOSE 9870 9864 8088 8042 19888 8020

CMD ["/start-hadoop.sh"]