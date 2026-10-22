#!/bin/bash
# mariadb/script.sh

echo "Configurando S3FS e montando bucket RAW do MinIO..."
yum install -y epel-release && yum install -y s3fs-fuse
echo admin:admin123 > /etc/passwd-s3fs && chmod 600 /etc/passwd-s3fs
mkdir -p /mnt/minio_raw
s3fs raw /mnt/minio_raw -o passwd_file=/etc/passwd-s3fs -o url=http://minio:9000 -o use_path_request_style -o allow_other

echo "Iniciando o MariaDB em background..."
/usr/local/bin/docker-entrypoint.sh mariadbd &
MARIADB_PID=$!

echo "Aguardando o MariaDB aceitar conexões..."
while ! mysqladmin ping -h"localhost" -uroot -proot --silent; do
    sleep 2
done
echo "MariaDB online!"

echo "Aguardando o Kafka Connect depositar o primeiro arquivo Parquet no S3..."
# A Engine CONNECT do MariaDB falha ao criar a tabela se não houver um arquivo parquet 
# para ele deduzir o schema na pasta mapeada.
while true; do
    PARQUET_FILES=$(find /mnt/minio_raw -type f -name "*.parquet" 2>/dev/null)
    if [ -n "$PARQUET_FILES" ]; then
        break
    fi
    echo "Arquivos Parquet não encontrados. Aguardando 15 segundos (O flush no connect tá pra 2 min)..."
    sleep 15
done
echo "Primeiro arquivo Parquet detectado!"

echo "Executando init.sql (Criação de Tabelas Externas e Views)..."
mysql -uroot -proot < /init.sql

echo "Tabelas e Views criadas com sucesso! Processo 100% automatizado concluído."

# Mantém o container rodando amarrado ao PID do banco
wait $MARIADB_PID
