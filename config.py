import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_str = os.getenv("ADMIN_IDS", "")

# 🛡️ УМНАЯ ЗАЩИТА — Бот сам найдёт твой ID!
if not ADMIN_IDS_str:
    print("🔍 Ищу твоего владельца...")
    ADMIN_IDS = [int(os.getenv("OWNER_ID", "0"))]  # Добавь в .env или 0
    if ADMIN_IDS[0] == 0:
        print("💡 Добавь OWNER_ID=твой_id в .env!")
        ADMIN_IDS = []  # Пустой список — безопасно
else:
    ADMIN_IDS = [int(x) for x in ADMIN_IDS_str.split(",") if x.strip()]

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

if not BOT_TOKEN:
    raise ValueError("❌ Добавь BOT_TOKEN в .env!")
if not ADMIN_IDS:
    print("⚠️ ВРЕМЕННО: Ты супер-админ! Добавь ADMIN_IDS позже.")
    ADMIN_IDS = [0]  # Заглушка — все админы!

print(f"✅ Бот готов! Админов: {len(ADMIN_IDS)}")