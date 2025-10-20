from aiogram import Bot
from config import ADMIN_IDS

async def notify_admins(bot: Bot, message: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message)
        except Exception as e:
            print(f"❌ Ошибка уведомления админа {admin_id}: {e}")

async def notify_user(bot: Bot, user_id: int, message: str):
    try:
        await bot.send_message(user_id, message)
    except Exception as e:
        print(f"❌ Ошибка уведомления пользователя {user_id}: {e}")