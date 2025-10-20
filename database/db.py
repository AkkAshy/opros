import aiosqlite
from datetime import datetime
import os
from config import MEDIA_DIR

DB_FILE = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'user'  -- 'user' или 'admin'
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS appeals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                phone TEXT,
                full_name TEXT,
                address TEXT,
                domkom TEXT,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'unprocessed',  -- 'unprocessed' или 'processed'
                comment TEXT  -- Опциональный комментарий админа
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appeal_id INTEGER,
                file_path TEXT,
                file_type TEXT  -- 'photo' или 'video'
            )
        ''')
        await db.commit()

async def add_user(telegram_id: int, role: str = 'user'):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, role) VALUES (?, ?)",
            (telegram_id, role)
        )
        await db.commit()

async def update_user_role(telegram_id: int, role: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?",
            (role, telegram_id)
        )
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT telegram_id, role FROM users ORDER BY telegram_id")
        return list(await cursor.fetchall())

async def is_admin(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT role FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return row is not None and row[0] == 'admin'

async def create_appeal(data: dict) -> int:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            """INSERT INTO appeals (user_id, phone, full_name, address, domkom, text)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data['user_id'], data['phone'], data['full_name'], data['address'], data['domkom'], data['text'])
        )
        await db.commit()
        lastrowid = cursor.lastrowid
        if lastrowid is None:
            raise ValueError("Failed to create appeal")
        return lastrowid

async def add_media(appeal_id: int, file_path: str, file_type: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO media (appeal_id, file_path, file_type) VALUES (?, ?, ?)",
            (appeal_id, file_path, file_type)
        )
        await db.commit()

async def get_appeals(status: str, page: int = 1, per_page: int = 5) -> list:
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT * FROM appeals WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, per_page, offset)
        )
        return list(await cursor.fetchall())

async def get_total_pages(status: str, per_page: int = 5) -> int:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM appeals WHERE status = ?", (status,))
        result = await cursor.fetchone()
        if result is None:
            return 0
        count = result[0]
        return (count + per_page - 1) // per_page

async def get_appeal(appeal_id: int) -> dict | None:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT * FROM appeals WHERE id = ?", (appeal_id,))
        appeal = await cursor.fetchone()
        if not appeal:
            return None
        columns = [col[0] for col in cursor.description]
        appeal_dict = dict(zip(columns, appeal))

        cursor = await db.execute("SELECT file_path, file_type FROM media WHERE appeal_id = ?", (appeal_id,))
        media = await cursor.fetchall()
        appeal_dict['media'] = [{'path': m[0], 'type': m[1]} for m in media]
        return appeal_dict

async def process_appeal(appeal_id: int, comment: str | None = None):
    async with aiosqlite.connect(DB_FILE) as db:
        if comment:
            await db.execute("UPDATE appeals SET status = 'processed', comment = ? WHERE id = ?", (comment, appeal_id))
        else:
            await db.execute("UPDATE appeals SET status = 'processed' WHERE id = ?", (appeal_id,))
        await db.commit()

async def get_unprocessed_count() -> int:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM appeals WHERE status = 'unprocessed'")
        result = await cursor.fetchone()
        if result is None:
            return 0
        return result[0]