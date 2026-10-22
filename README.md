# shopvibe
ShopVibe: Ingestão de Dados em Tempo Real


# ADR-[20261020]: [Dados em Real Time]

* **Status:** [Proposto | Aceito | Rejeitado | Substituído]
* **Data:** [20/10/2026]
* **Autor(es):** [Matheus Rodrigues Hilario / Engenheiro de Dados]
* **Decisores:** [Matheus Rodrigues Hilario / Engenheiros envolvidos]

## Contexto
ShopVibe é um e-commerce fictício que perde vendas por não enxergar o que acontece na loja em tempo real. A missão é propor, documentar e demonstrar a ingestão em tempo real dos pedidos da loja. (ex: volume de dados, latência, custos, restrições de conformidade como LGPD/GDPR).

## Decisão
Decidimos usar o Kafka conect debezium por necessidade de baixissima latencia, alta vazão de volumetria e também pelo mesmo conseguir se conectar com o MinIO S3 e com o MongoDB, aqui estamos fazendo CDC pois sabemos que o banco de produção não aguentaria as regras de negócio inputadas direto na fonte, usamos aqui para fazer a replica para o tópico "pgserver.public.orders" onde conseguimos ler esses dados, também fazemos uso do schema-registry ou seja os metadados dos dados vão junto com a mensagem ou seja sabemos o tipo certo de cada campo (INT, STRING, FLOAT, TIMESTAMP), fazemos o sink com o MinIO S3 e MongoDB com replicaSet habilitado ou seja podemos usar um Metabase para criar as visualizações e criamos uma API FastAPI Async para consumo de dados com documentação (Swagger e Redoc)

Explique de forma clara e direta qual foi a escolha arquitetônica adotada. 
*Ex: "Decidimos adotar o Apache Iceberg como formato de tabela padrão no Data Lakehouse em vez de Delta Lake."*

## Consequências
Quais são os impactos (positivos e negativos) decorrentes desta decisão?

### Positivas (Prós)
* Permite portabilidade entre múltiplos mecanismos de consulta (Trino, Spark).
* Facilita o controle de concorrência e transações ACID.

### Negativas / Riscos (Contras)
* Curva de aprendizado inicial da equipe para o formato Iceberg.
* Necessidade de ajustes nos pipelines legados.

## Alternativas Consideradas
Quais outras opções foram avaliadas e por que foram descartadas?
1. **[Alternativa A]:** Descartada devido a [motivo, ex: alto custo de licenciamento].
2. **[Alternativa B]:** Descartada devido a [motivo, ex: falta de suporte nativo à feature X].
