from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def get_back_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Orqaga"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_media_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Keyingi"), KeyboardButton(text="🔙 Orqaga"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_main_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📝 Murojaat yaratish")]],
        resize_keyboard=True
    )


def get_main_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Murojaat yaratish")],
            [KeyboardButton(text="👑 Admin panel")]
        ],
        resize_keyboard=True
    )

def get_phone_keyboard():
    """📱 Кнопка отправки номера — МГНОВЕННО!"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True  # Исчезает после нажатия
    )