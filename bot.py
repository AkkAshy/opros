import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # Или Redis для продакшена
from config import BOT_TOKEN
from database.db import init_db
from handlers.user import router as user_router
from handlers.admin import router as admin_router

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()

    if BOT_TOKEN is None:
        raise ValueError("❌ BOT_TOKEN не найден в .env!")
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()  # Для FSM
    dp = Dispatcher(storage=storage)
    
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    print("🌟 Бот запущен! Ждёт обращений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())