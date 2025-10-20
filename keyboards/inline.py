from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_preview_buttons(appeal_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"confirm_{appeal_id}")
    builder.button(text="✏️ Tahrirlash", callback_data="edit")
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(1)  # По одной в столбик
    return builder.as_markup()

def get_admin_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Ishlanmagan", callback_data="unprocessed")
    builder.button(text="📤 Ishlangan", callback_data="processed")
    builder.button(text="👥 Adminlarni boshqarish", callback_data="manage_admins")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_management_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Admin qo'shish", callback_data="add_admin")
    builder.button(text="📋 Adminlar ro'yxati", callback_data="list_admins")
    builder.button(text="🔙 Orqaga", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_appeals_list_buttons(appeals: list, page: int, total_pages: int, is_unprocessed: bool):
    builder = InlineKeyboardBuilder()
    for appeal in appeals:
        builder.button(text=f"№{appeal['id']} - {appeal['created_at'][:10]}", callback_data=f"view_{appeal['id']}")
    if page > 1:
        builder.button(text="◀️ Oldingi", callback_data=f"prev_{'un' if is_unprocessed else 'pr'}_{page-1}")
    if page < total_pages:
        builder.button(text="▶️ Keyingi", callback_data=f"next_{'un' if is_unprocessed else 'pr'}_{page+1}")
    builder.button(text="🔙 Menyuga", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_appeal_actions(appeal_id: int, is_unprocessed: bool):
    builder = InlineKeyboardBuilder()
    if is_unprocessed:
        builder.button(text="✅ Ishlash", callback_data=f"process_{appeal_id}")
        builder.button(text="💬 Izoh qo'shish", callback_data=f"comment_{appeal_id}")
    builder.button(text="� Ro'yxatga", callback_data="back_to_list")
    builder.adjust(1)
    return builder.as_markup()