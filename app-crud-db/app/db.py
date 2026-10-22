from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Depends
from .configs import settings

client = AsyncIOMotorClient(settings.DB_URL)


async def get_session() -> AsyncIOMotorDatabase:
    # Atualizado para o banco correto
    db = client.analytics_db
    yield db


ActiveSession = Depends(get_session)
