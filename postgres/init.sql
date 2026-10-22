-- postgres/init.sql
-- Este script é executado automaticamente quando o container PostgreSQL sobe.
-- CREATE USER kafkacdc WITH PASSWORD 'kafkacdc';
-- CREATE DATABASE shop;

-- GRANT ALL PRIVILEGES ON DATABASE shop TO kafkacdc;
-- ALTER DATABASE shop OWNER TO postgres;


\c postgres

-- CREATE TABLE IF NOT EXISTS orders (
--     order_id SERIAL PRIMARY KEY,
--     customer_id INT,
--     total DECIMAL(10,2),
--     status VARCHAR(50),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );


CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    items JSONB NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Habilita o CDC completo para a tabela
ALTER TABLE orders REPLICA IDENTITY FULL;

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kafkacdc;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
