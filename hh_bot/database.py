from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import config
from models import Base
from typing import AsyncGenerator
import os

engine = create_async_engine(config.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    # Создаем базу данных только если она не существует
    if not os.path.exists('database.sqlite3'):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("База данных успешно создана")
    else:
        print("База данных уже существует")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session 