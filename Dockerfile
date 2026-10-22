ARG STRIMZI_VERSION=latest-kafka-3.7.0

# -----------------------------------------------------------------------------
# Etapa 1 (temporária): baixa e descompacta os plugins em .zip (S3 Sink, MongoDB e Avro)
# -----------------------------------------------------------------------------
FROM debian:latest AS unzip-layer

RUN apt-get update && apt-get install -y unzip curl

WORKDIR /tmp/connect-plugins

# Baixa e descompacta o S3 Sink
RUN curl -sfSL https://api.hub.confluent.io/api/plugins/confluentinc/kafka-connect-s3/versions/10.5.5/archive -o s3-archive.zip &&\
    unzip s3-archive.zip

# Baixa e descompacta o MongoDB Sink
RUN curl -sfSL https://api.hub.confluent.io/api/plugins/mongodb/kafka-connect-mongodb/versions/1.13.0/archive -o mongo-archive.zip &&\
    unzip mongo-archive.zip

# Baixa e descompacta o Avro Converter (CORREÇÃO DO ERRO)
RUN curl -sfSL https://api.hub.confluent.io/api/plugins/confluentinc/kafka-connect-avro-converter/versions/7.3.0/archive -o avro-archive.zip &&\
    unzip avro-archive.zip


# -----------------------------------------------------------------------------
# Etapa 2 (imagem final): Kafka Connect do Strimzi + plugins
# -----------------------------------------------------------------------------
FROM quay.io/strimzi/kafka:${STRIMZI_VERSION} AS imagemfinal

ARG DEBEZIUM_CONNECTOR_VERSION=2.6.1.Final

# Pasta onde o Kafka Connect procura os plugins (plugin.path)
ENV KAFKA_CONNECT_PLUGIN_PATH=/tmp/connect-plugins/
ENV KAFKA_CONNECT_LIBS=/opt/kafka/libs

# Plugins Debezium (Source / CDC): PostgreSQL e SQL Server
# + Debezium Interceptor (usado para tracing)
RUN mkdir $KAFKA_CONNECT_PLUGIN_PATH &&\
    cd $KAFKA_CONNECT_PLUGIN_PATH &&\
    curl -sfSL  https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/${DEBEZIUM_CONNECTOR_VERSION}/debezium-connector-postgres-${DEBEZIUM_CONNECTOR_VERSION}-plugin.tar.gz | tar xz &&\
    cd debezium-connector-postgres &&\
    curl -sfSL  https://repo1.maven.org/maven2/io/debezium/debezium-connector-sqlserver/${DEBEZIUM_CONNECTOR_VERSION}/debezium-connector-sqlserver-${DEBEZIUM_CONNECTOR_VERSION}-plugin.tar.gz | tar xz &&\
    cd debezium-connector-sqlserver &&\
    curl -sfSL https://repo1.maven.org/maven2/io/debezium/debezium-interceptor/${DEBEZIUM_CONNECTOR_VERSION}/debezium-interceptor-${DEBEZIUM_CONNECTOR_VERSION}.jar -o debezium-interceptor-${DEBEZIUM_CONNECTOR_VERSION}.jar

# Copia os plugins (Etapa 1) para a pasta de plugins
COPY --from=unzip-layer /tmp/connect-plugins/confluentinc-kafka-connect-s3-10.5.5 ${KAFKA_CONNECT_PLUGIN_PATH}/confluentinc-kafka-connect-s3-10.5.5
COPY --from=unzip-layer /tmp/connect-plugins/mongodb-kafka-connect-mongodb-1.13.0 ${KAFKA_CONNECT_PLUGIN_PATH}/mongodb-kafka-connect-mongodb-1.13.0
COPY --from=unzip-layer /tmp/connect-plugins/confluentinc-kafka-connect-avro-converter-7.3.0 ${KAFKA_CONNECT_PLUGIN_PATH}/confluentinc-kafka-connect-avro-converter-7.3.0