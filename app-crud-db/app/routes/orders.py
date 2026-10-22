# from fastapi import HTTPException, status, APIRouter
# from typing import Any, List
# from bson.decimal128 import Decimal128
# from pymongo import ReturnDocument
# from bson.errors import InvalidId
# from motor.motor_asyncio import AsyncIOMotorDatabase

# from app.models.orders import Orders, OrdersResponse, OrdersRequest
# from app.db import ActiveSession
# import json

# router = APIRouter()


# def serialize_mongo_doc(doc: dict) -> dict:
#     if not doc:
#         return doc

#     # Extrai o conteúdo da chave 'after' (se existir).
#     resultado = doc.get("after", doc).copy()

#     # Pega o _id da raiz do documento original e injeta no resultado como string
#     if "_id" in doc:
#         resultado["_id"] = str(doc["_id"])

#     # Corrige a divergência de nome: se veio 'items' do banco, renomeia para 'itens'
#     if "items" in resultado and "itens" not in resultado:
#         resultado["itens"] = resultado.pop("items")

#     # Converte tipos BSON e formata os campos
#     for key, value in list(resultado.items()):
#         if isinstance(value, Decimal128):
#             resultado[key] = float(value.to_decimal())
#         elif key in ("created_at", "updated_at") and value is not None:
#             if not isinstance(value, str):
#                 resultado[key] = str(value)
#         elif key == "itens" and isinstance(value, str):
#             # Se vier como string JSON do Debezium, converte para lista do Python
#             resultado[key] = json.loads(value)

#     return resultado


# @router.get("/")
# async def home():
#     return "Olá usuario"


# @router.get(
#     "/Orderss/", response_model=List[OrdersResponse], status_code=status.HTTP_200_OK
# )
# async def Consultar_Orderss_ID(session: AsyncIOMotorDatabase = ActiveSession) -> Any:
#     # Ignora registros marcados como deletados (op == 'd')
#     cursor = session["orders_agg"].find({"op": {"$ne": "d"}})
#     _Orderss = await cursor.to_list(length=1000)

#     return [serialize_mongo_doc(order) for order in _Orderss]


# @router.get(
#     "/Orderss/{idOrders}", response_model=OrdersResponse, status_code=status.HTTP_200_OK
# )
# async def Consultar_Orders(
#     idOrders: int, session: AsyncIOMotorDatabase = ActiveSession
# ) -> Any:
#     try:
#         query_id = int(idOrders)
#     except InvalidId:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido"
#         )

#     # Busca o evento mais recente daquele pedido que não seja uma deleção (op != 'd')
#     _Orders = await session["orders_agg"].find_one(
#         {
#             "after.order_id": query_id,
#             "op": {"$ne": "d"},
#         },
#         sort=[("ts_ms", -1)],
#     )

#     if _Orders is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Orders não encontrado"
#         )

#     return serialize_mongo_doc(_Orders)


# @router.post(
#     "/Orderss", response_model=OrdersResponse, status_code=status.HTTP_201_CREATED
# )
# async def Inserir_Orders(
#     order_in: OrdersRequest, session: AsyncIOMotorDatabase = ActiveSession
# ) -> Any:
#     order_dict = order_in.dict()

#     # Coloca os dados dentro da chave "after" para manter o padrão CDC
#     novo_documento = {"after": order_dict, "op": "c"}

#     await session["orders_agg"].insert_one(novo_documento)

#     return serialize_mongo_doc(novo_documento)


# @router.put(
#     "/Orderss/{idOrders}", response_model=OrdersResponse, status_code=status.HTTP_200_OK
# )
# async def Atualizar_Orders(
#     idOrders: int,
#     order_in: OrdersRequest,
#     session: AsyncIOMotorDatabase = ActiveSession,
# ) -> Any:
#     try:
#         query_id = int(idOrders)
#     except ValueError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido"
#         )

#     update_data = order_in.dict(exclude_unset=True)

#     # 1. Corrige o mapeamento: se o model enviou 'itens', converte para 'items' do banco
#     if "itens" in update_data:
#         update_data["items"] = update_data.pop("itens")

#     # 2. Usa "after.campo" no $set por causa da estrutura aninhada do Debezium
#     set_query = {f"after.{key}": value for key, value in update_data.items()}

#     # 3. Filtro flexível: busca tanto se o order_id for int quanto str, ignorando deletados
#     query_filter = {
#         "$or": [{"after.order_id": query_id}, {"after.order_id": str(query_id)}],
#         "op": {"$ne": "d"},
#     }

#     db_Orders = await session["orders_agg"].find_one_and_update(
#         query_filter,
#         {"$set": set_query},
#         sort=[("ts_ms", -1)],
#         return_document=ReturnDocument.AFTER,
#     )

#     if db_Orders is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Orders não encontrado"
#         )

#     return serialize_mongo_doc(db_Orders)


# @router.delete(
#     "/Orderss/{idOrders}", response_model=OrdersResponse, status_code=status.HTTP_200_OK
# )
# async def Deletar_Orders(
#     idOrders: int, session: AsyncIOMotorDatabase = ActiveSession
# ) -> Any:
#     try:
#         query_id = int(idOrders)
#     except InvalidId:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido"
#         )

#     # Atualizado para buscar pelo formato aninhado "after.order_id"
#     db_Orders = await session["orders_agg"].find_one_and_delete(
#         {"after.order_id": query_id}
#     )

#     if db_Orders is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Orders não encontrado"
#         )

#     return serialize_mongo_doc(db_Orders)
from fastapi import HTTPException, status, APIRouter
from typing import Any, List
from bson.decimal128 import Decimal128
from pymongo import ReturnDocument
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
import base64
from decimal import Decimal

from app.models.orders import Orders, OrdersResponse, OrdersRequest
from app.db import ActiveSession
import json

router = APIRouter()


def decode_kafka_decimal(b64_str: str) -> float:
    """Decodifica o formato de Decimal do Kafka Connect armazenado em bytes/Base64."""
    try:
        if not b64_str:
            return 0.0
        # O Kafka Connect serializa decimais como bytes em base64.
        # Convertemos para int e aplicamos a escala padrão de 2 casas decimais.
        decoded_bytes = base64.b64decode(b64_str)
        int_val = int.from_bytes(decoded_bytes, byteorder="big", signed=True)
        return float(Decimal(int_val) / Decimal(10**2))
    except Exception:
        return 0.0


def serialize_mongo_doc(doc: dict) -> dict:
    if not doc:
        return doc

    # Extrai o conteúdo da chave 'payload' (onde estão os dados reais do Kafka Connect)
    resultado = doc.get("payload", doc).copy()

    # Injeção do _id da raiz do documento original convertida para string
    if "_id" in doc:
        resultado["_id"] = str(doc["_id"])

    # Tratamento da flag de deleção do Kafka Connect (__deleted)
    if resultado.get("__deleted") == "true":
        resultado["__deleted"] = True
    else:
        resultado["__deleted"] = False

    # Corrige a divergência de nome: se veio 'items' do banco, renomeia para 'itens'
    if "items" in resultado and "itens" not in resultado:
        resultado["itens"] = resultado.pop("items")

    # Tratamento e conversão de tipos específicos do payload
    for key, value in list(resultado.items()):
        if key == "total" and isinstance(value, str):
            resultado[key] = decode_kafka_decimal(value)
        elif key == "itens" and isinstance(value, str):
            try:
                resultado[key] = json.loads(value)
            except json.JSONDecodeError:
                pass
        elif key in ("created_at", "updated_at") and value is not None:
            if not isinstance(value, str):
                resultado[key] = str(value)

    return resultado


@router.get("/")
async def home():
    return "Olá usuário"


@router.get(
    "/Orderss/", response_model=List[OrdersResponse], status_code=status.HTTP_200_OK
)
async def Consultar_Orderss_ID(session: AsyncIOMotorDatabase = ActiveSession) -> Any:
    # Ignora registros marcados como deletados (__deleted != 'true')
    cursor = session["orders_agg"].find({"payload.__deleted": {"$ne": "true"}})
    _Orderss = await cursor.to_list(length=1000)

    return [serialize_mongo_doc(order) for order in _Orderss]


@router.get(
    "/Orderss/{idOrders}", response_model=OrdersResponse, status_code=status.HTTP_200_OK
)
async def Consultar_Orders(
    idOrders: int, session: AsyncIOMotorDatabase = ActiveSession
) -> Any:
    try:
        query_id = int(idOrders)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido"
        )

    # Busca o evento mais recente dentro do payload que não esteja deletado
    _Orders = await session["orders_agg"].find_one(
        {
            "$or": [
                {"payload.order_id": query_id},
                {"payload.order_id": str(query_id)},
            ],
            "payload.__deleted": {"$ne": "true"},
        },
        sort=[("payload.__source_ts_ms", -1)],
    )

    if _Orders is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orders não encontrado"
        )

    return serialize_mongo_doc(_Orders)


@router.post(
    "/Orderss", response_model=OrdersResponse, status_code=status.HTTP_201_CREATED
)
async def Inserir_Orders(
    order_in: OrdersRequest, session: AsyncIOMotorDatabase = ActiveSession
) -> Any:
    order_dict = order_in.dict()

    # Estrutura padrão com payload para simular o sink do Kafka Connect
    novo_documento = {"payload": {**order_dict, "__op": "c", "__deleted": "false"}}

    await session["orders_agg"].insert_one(novo_documento)

    return serialize_mongo_doc(novo_documento)


@router.put(
    "/Orderss/{idOrders}", response_model=OrdersResponse, status_code=status.HTTP_200_OK
)
async def Atualizar_Orders(
    idOrders: int,
    order_in: OrdersRequest,
    session: AsyncIOMotorDatabase = ActiveSession,
) -> Any:
    try:
        query_id = int(idOrders)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido"
        )

    update_data = order_in.dict(exclude_unset=True)

    if "itens" in update_data:
        update_data["items"] = update_data.pop("itens")

    # Atualiza os campos dentro de "payload."
    set_query = {f"payload.{key}": value for key, value in update_data.items()}
    set_query["payload.__op"] = "u"

    query_filter = {
        "$or": [{"payload.order_id": query_id}, {"payload.order_id": str(query_id)}],
        "payload.__deleted": {"$ne": "true"},
    }

    db_Orders = await session["orders_agg"].find_one_and_update(
        query_filter,
        {"$set": set_query},
        sort=[("payload.__source_ts_ms", -1)],
        return_document=ReturnDocument.AFTER,
    )

    if db_Orders is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orders não encontrado"
        )

    return serialize_mongo_doc(db_Orders)


@router.delete(
    "/Orderss/{idOrders}", response_model=OrdersResponse, status_code=status.HTTP_200_OK
)
async def Deletar_Orders(
    idOrders: int, session: AsyncIOMotorDatabase = ActiveSession
) -> Any:
    try:
        query_id = int(idOrders)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido"
        )

    query_filter = {
        "$or": [{"payload.order_id": query_id}, {"payload.order_id": str(query_id)}]
    }

    # Soft delete simulando o comportamento de CDC/Sink (__deleted = 'true')
    db_Orders = await session["orders_agg"].find_one_and_update(
        query_filter,
        {"$set": {"payload.__deleted": "true", "payload.__op": "d"}},
        return_document=ReturnDocument.AFTER,
    )

    if db_Orders is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orders não encontrado"
        )

    return serialize_mongo_doc(db_Orders)
