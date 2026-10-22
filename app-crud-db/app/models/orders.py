from typing import Optional
from pydantic import BaseModel, Field


# 1. Criamos um modelo Base com os campos comuns para evitar repetição
class OrdersBase(BaseModel):
    customer_id: int
    total: float
    itens: list
    status: str
    created_at: str
    updated_at: str


# 2. Modelo principal da aplicação (Substitui o SQLModel table=True)
class Orders(OrdersBase):
    # No MongoDB não existe o conceito de primary_key=True do SQL.
    # O MongoDB gerencia sua própria chave primária chamada "_id".
    order_id: Optional[int]


# 3. Modelo usado para enviar as respostas da API para o cliente
class OrdersResponse(OrdersBase):
    # Aqui o order_id é obrigatório, garantindo que a resposta sempre devolva o ID
    order_id: int


# 4. Modelo para receber requisições de criação (se você precisar)
class OrdersRequest(OrdersBase):
    pass
