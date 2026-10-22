# #!/bin/bash
# # postgres/script.sh

# echo "Aguardando o PostgreSQL iniciar e a tabela orders ser criada pelo init.sql..."
# sleep 15

# echo "Iniciando emulador de base viva (5000 linhas, lotes de 1000 a cada 5 min)..."

# for i in {1..50}; do
#   echo "Inserindo lote $i de 50..."
#   PGPASSWORD=postgres psql -h pgvector -U postgres -d postgres -c "
#     INSERT INTO orders (customer_id, total, status, created_at)
#     SELECT 
#       floor(random() * 1000 + 1)::INT,
#       (random() * 500 + 10)::DECIMAL(10,2),
#       CASE WHEN random() > 0.5 THEN 'COMPLETED' ELSE 'PENDING' END,
#       NOW() - (random() * interval '280 days')
#     FROM generate_series(1, 1000);
#   "
#   sleep 30 # Aguarda 5 minutos
# done

# echo "Carga de dados finalizada."


#!/bin/bash

# Configurações do Banco de Dados PostgreSQL
DB_HOST="${DB_HOST:-pgvector}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
export PGPASSWORD="${PGPASSWORD:-postgres}"

PSQL="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -A -c"

STATUSES=("pending" "processing" "shipped" "delivered" "cancelled")

echo "Starting transactional load simulation on PostgreSQL..."

for i in $(seq 1 20000); do
  # 1. INSERT: Gera dados usando awk (não precisa do bc)
  ORDER_ID="$((100 + RANDOM % 1525))"
  CUST_ID="$((100 + RANDOM % 900))"
  PROD_ID="$((1000 + RANDOM % 9000))"
  QTY=$((1 + RANDOM % 5))
  
  # Cálculo de preço e total usando AWK
  PRICE=$(awk -v r1=$RANDOM 'BEGIN { printf "%.2f", (10 + (r1 % 100)) + 0.99 }')
  TOTAL=$(awk -v q=$QTY -v p=$PRICE 'BEGIN { printf "%.2f", q * p }')

  ITEMS_JSON="[{\"product_id\": \"$PROD_ID\", \"quantity\": $QTY, \"price\": $PRICE}]"

  INSERT_SQL="INSERT INTO orders (order_id, customer_id, status, items, total, created_at, updated_at) 
              VALUES ($ORDER_ID, $CUST_ID, 'pending', '$ITEMS_JSON'::jsonb, $TOTAL, NOW(), NOW());"
  
  $PSQL "$INSERT_SQL" > /dev/null
  echo "[INSERT] Created order $ORDER_ID (Customer: $CUST_ID, Total: $TOTAL)"

  # 2. UPDATE: Seleciona um pedido aleatório existente e atualiza o status usando order_id
  RANDOM_STATUS="${STATUSES[$RANDOM % ${#STATUSES[@]}]}"
  
  UPDATE_SQL="UPDATE orders 
              SET status = '$RANDOM_STATUS', updated_at = NOW() 
              WHERE order_id IN (SELECT order_id FROM orders ORDER BY RANDOM() LIMIT 1);"
  
  $PSQL "$UPDATE_SQL" > /dev/null
  echo "[UPDATE] Updated random order status to '$RANDOM_STATUS'"

  sleep 5
done

echo "Simulation finished successfully!"