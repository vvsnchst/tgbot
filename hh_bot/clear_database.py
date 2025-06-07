import os
import asyncio
from database import engine, Base

async def clear_database():
    # Проверяем существование базы данных
    if os.path.exists('database.sqlite3'):
        # Удаляем старую базу данных
        os.remove('database.sqlite3')
        print("Старая база данных удалена")
    
    # Создаем новую базу данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Новая база данных успешно создана")

if __name__ == "__main__":
    asyncio.run(clear_database()) 