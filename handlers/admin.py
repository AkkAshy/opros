import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InaccessibleMessage
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db import is_admin, get_appeals, get_total_pages, get_appeal, process_appeal, get_unprocessed_count, update_user_role, get_all_users
from keyboards.inline import get_admin_menu, get_appeals_list_buttons, get_appeal_actions, get_admin_management_menu
from states.appeal import AdminForm
from utils.notifications import notify_admins, notify_user
from utils.statistics import create_excel_export_async

router = Router()

async def check_admin(message: Message):
    if message.from_user is None or not await is_admin(message.from_user.id):
        await message.answer("Доступ только админам.")
        return False
    return True

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not await check_admin(message):
        return
    count = await get_unprocessed_count()
    await message.answer(f"Admin panel. Ishlanmagan: {count}", reply_markup=get_admin_menu())

@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        await callback.answer("❌ Xabar topilmadi.")
        return
    count = await get_unprocessed_count()
    await callback.message.edit_text(f"Admin panel. Ishlanmagan: {count}", reply_markup=get_admin_menu())
    await callback.answer()

@router.callback_query(F.data.in_({"unprocessed", "processed"}))
async def show_appeals_list(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        await callback.answer("❌ Xabar topilmadi.")
        return
    is_unprocessed = callback.data == "unprocessed"
    status = "unprocessed" if is_unprocessed else "processed"
    page = 1
    appeals = await get_appeals(status, page)
    total_pages = await get_total_pages(status)

    appeals_list = [{'id': a[0], 'created_at': a[6]} for a in appeals]  # id и дата

    await callback.message.edit_text(
        f"{'Ishlanmagan' if is_unprocessed else 'Ishlangan'} murojaatlar (sahifa {page}/{total_pages}):",
        reply_markup=get_appeals_list_buttons(appeals_list, page, total_pages, is_unprocessed)
    )
    await state.update_data(is_unprocessed=is_unprocessed)  # Для back
    await callback.answer()

@router.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def paginate_appeals(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage) or callback.data is None:
        await callback.answer("❌ Ma'lumotlar topilmadi.")
        return
    parts = callback.data.split("_")
    is_un = parts[1] == "un"
    page = int(parts[2])
    status = "unprocessed" if is_un else "processed"
    appeals = await get_appeals(status, page)
    total_pages = await get_total_pages(status)

    appeals_list = [{'id': a[0], 'created_at': a[6]} for a in appeals]

    await callback.message.edit_text(
        f"{'Ishlanmagan' if is_un else 'Ishlangan'} (sahifa {page}/{total_pages}):",
        reply_markup=get_appeals_list_buttons(appeals_list, page, total_pages, is_un)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_"))
async def view_appeal(callback: CallbackQuery, bot: Bot):
    if callback.data is None or callback.message is None or isinstance(callback.message, InaccessibleMessage) or callback.from_user is None:
        await callback.answer("❌ Ma'lumotlar topilmadi.")
        return
    appeal_id = int(callback.data.split("_")[1])
    appeal = await get_appeal(appeal_id)
    if not appeal:
        await callback.answer("Murojaat topilmadi.")
        return

    text = f"""
<b>Murojaat №{appeal['id']}</b>
Sana: {appeal['created_at']}
Telefon: {appeal['phone']}
F.I.O.: {appeal['full_name']}
Manzil: {appeal['address']}
Uy MFI/OFI: {appeal['domkom']}
Matn: {appeal['text']}
Status: {'Ishlanmagan' if appeal['status'] == 'unprocessed' else 'Ishlangan'}
Izoh: {appeal.get('comment', "Yo'q")}
"""
    await callback.message.edit_text(text, parse_mode="HTML")

    for m in appeal['media']:
        if m['type'] == 'photo':
            await bot.send_photo(callback.from_user.id, FSInputFile(m['path']))
        elif m['type'] == 'video':
            await bot.send_video(callback.from_user.id, FSInputFile(m['path']))

    is_unprocessed = appeal['status'] == 'unprocessed'
    await bot.send_message(callback.from_user.id, "Harakatlar:", reply_markup=get_appeal_actions(appeal_id, is_unprocessed))
    await callback.answer()

@router.callback_query(F.data.startswith("process_"))
async def process_appeal_handler(callback: CallbackQuery, bot: Bot):
    if callback.data is None or callback.message is None:
        await callback.answer("❌ Ma'lumotlar topilmadi.")
        return
    appeal_id = int(callback.data.split("_")[1])
    appeal = await get_appeal(appeal_id)
    if not appeal:
        await callback.answer("Murojaat topilmadi.")
        return
    await process_appeal(appeal_id)
    await notify_user(bot, appeal['user_id'], f"Sizning murojaatingiz №{appeal_id} ko'rib chiqish uchun qabul qilindi.")
    await callback.message.answer("Murojaat ishlandi!")
    await callback.answer()

@router.callback_query(F.data == "manage_admins")
async def show_admin_management(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        await callback.answer("❌ Xabar topilmadi.")
        return
    await callback.message.edit_text("Adminlarni boshqarish:", reply_markup=get_admin_management_menu())
    await callback.answer()

@router.callback_query(F.data == "add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        await callback.answer("❌ Xabar topilmadi.")
        return
    await callback.message.edit_text("Admin qilmoqchi bo'lgan foydalanuvchi ID sini yuboring:")
    await state.set_state(AdminForm.waiting_for_user_id)
    await callback.answer()

@router.message(AdminForm.waiting_for_user_id)
async def add_admin_process(message: Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Ruxsat berilmagan.")
        return

    if message.text is None:
        await message.answer("❌ Matn topilmadi.")
        return

    try:
        user_id = int(message.text.strip())
        await update_user_role(user_id, 'admin')
        await message.answer(f"✅ Foydalanuvchi {user_id} adminlarga qo'shildi!", reply_markup=get_admin_management_menu())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID formati. Raqam kiriting.", reply_markup=get_admin_management_menu())
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}", reply_markup=get_admin_management_menu())

    await state.clear()

@router.callback_query(F.data == "list_admins")
async def list_admins(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        await callback.answer("❌ Xabar topilmadi.")
        return

    users = await get_all_users()
    admin_list = []
    user_list = []

    for user_id, role in users:
        if role == 'admin':
            admin_list.append(f"👑 {user_id}")
        else:
            user_list.append(f"👤 {user_id}")

    text = "📋 Foydalanuvchilar ro'yxati:\n\n"
    if admin_list:
        text += "Adminlar:\n" + "\n".join(admin_list) + "\n\n"
    if user_list:
        text += "Foydalanuvchilar:\n" + "\n".join(user_list[:10])  # Показываем только первых 10
        if len(user_list) > 10:
            text += f"\n... va yana {len(user_list) - 10} foydalanuvchi"

    await callback.message.edit_text(text, reply_markup=get_admin_management_menu())
    await callback.answer()

@router.message(Command("export"))
async def export_command(message: Message):
    if not await check_admin(message):
        return

    await message.answer("📊 Eksport tayyorlanmoqda...")

    try:
        filepath = await create_excel_export_async()
        filename = os.path.basename(filepath)

        await message.answer_document(
            FSInputFile(filepath),
            caption=f"📊 Statistika fayli: {filename}"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@router.message(F.text == "👑 Admin panel")
async def admin_panel_button(message: Message):
    if not await check_admin(message):
        return
    count = await get_unprocessed_count()
    await message.answer(f"Admin panel. Ishlanmagan: {count}", reply_markup=get_admin_menu())

@router.callback_query(F.data.startswith("comment_"))
async def add_comment_start(callback: CallbackQuery, state: FSMContext):
    if callback.data is None or callback.message is None or isinstance(callback.message, InaccessibleMessage):
        await callback.answer("❌ Ma'lumotlar topilmadi.")
        return
    appeal_id = int(callback.data.split("_")[1])
    await state.update_data(appeal_id=appeal_id)
    await callback.message.edit_text("Izohni kiriting (yoki /skip agar izohsiz):")
    await state.set_state(AdminForm.waiting_for_comment)
    await callback.answer()

@router.message(AdminForm.waiting_for_comment)
async def add_comment_process(message: Message, state: FSMContext, bot: Bot):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Ruxsat berilmagan.")
        return

    data = await state.get_data()
    appeal_id = data.get('appeal_id')
    if not appeal_id:
        await message.answer("❌ Murojaat ID topilmadi.")
        await state.clear()
        return

    appeal = await get_appeal(appeal_id)
    if not appeal:
        await message.answer("❌ Murojaat topilmadi.")
        await state.clear()
        return

    comment = message.text.strip() if message.text and message.text != "/skip" else None
    await process_appeal(appeal_id, comment)
    await notify_user(bot, appeal['user_id'], f"Sizning murojaatingiz №{appeal_id} ko'rib chiqish uchun qabul qilindi." + (f"\nIzoh: {comment}" if comment else ""))
    await message.answer("Izoh qo'shildi va murojaat ishlandi!")
    await state.clear()

@router.callback_query(F.data == "export_stats")
async def export_statistics(callback: CallbackQuery):
    if callback.message is None or isinstance(callback.message, InaccessibleMessage):
        await callback.answer("❌ Xabar topilmadi.")
        return

    await callback.message.edit_text("📊 Eksport tayyorlanmoqda...")

    try:
        filepath = await create_excel_export_async()
        filename = os.path.basename(filepath)

        await callback.message.answer_document(
            FSInputFile(filepath),
            caption=f"📊 Statistika fayli: {filename}"
        )
        await callback.message.edit_text("✅ Eksport muvaffaqiyatli yakunlandi!", reply_markup=get_admin_menu())
    except Exception as e:
        await callback.message.edit_text(f"❌ Xatolik: {e}", reply_markup=get_admin_menu())

    await callback.answer()

@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_unprocessed = data.get('is_unprocessed', True)
    await show_appeals_list(callback, state)  # Переиспользуем