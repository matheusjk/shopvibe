-- mariadb/init.sql
-- Execute este script DENTRO do MariaDB após o pipeline estar rodando (para as views já terem dados para ler)
-- Habilita a engine Connect para ler arquivos fora do BD nativo
INSTALL SONAME 'ha_connect';

CREATE DATABASE IF NOT EXISTS datalake;
USE datalake;

-- 1. Cria a Tabela Externa (Direct Read S3 Parquet via FUSE)
CREATE TABLE orders_raw (
    order_id INT,
    customer_id INT,
    total DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP
) ENGINE=CONNECT TABLE_TYPE=PARQUET FILE_NAME='/mnt/minio_raw/topics/orders/*/*.parquet';

-- 2. Regra de Negócio: Total de pedidos semanais (Salvo como VIEW para o Metabase consumir fácil)
CREATE OR REPLACE VIEW vw_pedidos_semanais AS
SELECT 
    YEARWEEK(created_at, 1) AS semana,
    COUNT(order_id) AS total_pedidos_semana
FROM orders_raw
GROUP BY YEARWEEK(created_at, 1)
ORDER BY semana DESC;

-- 3. Regra de Negócio: Valor total vendido por semana e por status (Salvo como VIEW)
CREATE OR REPLACE VIEW vw_valor_vendido_semana AS
SELECT 
    YEARWEEK(created_at, 1) AS semana,
    status,
    SUM(total) AS valor_total_vendido
FROM orders_raw
GROUP BY YEARWEEK(created_at, 1), status
ORDER BY semana DESC;
