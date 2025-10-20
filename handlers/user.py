from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from database.db import add_user, create_appeal, add_media, is_admin
from states.appeal import AppealForm
from keyboards.reply import get_cancel_keyboard, get_back_cancel_keyboard, get_main_user_keyboard, get_main_admin_keyboard, get_phone_keyboard, get_media_keyboard
from keyboards.inline import get_preview_buttons
from utils.validators import validate_phone, clean_phone, validate_phone_clean
from utils.notifications import notify_admins
from config import MEDIA_DIR
import os
import uuid

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    await add_user(message.from_user.id)
    if await is_admin(message.from_user.id):
        await message.answer("Salom admin! Harakatni tanlang.", reply_markup=get_main_admin_keyboard())
    else:
        await message.answer("Xush kelibsiz! Murojaat yarating.", reply_markup=get_main_user_keyboard())

@router.message(F.text == "📝 Murojaat yaratish")
async def start_appeal(message: Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    if await is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(AppealForm.phone)
    await message.answer(
        "📱 <b>1-qadam: Telefon raqamingizni yuboring</b>\n\n"
        "Quyidagi tugmani bosing 👇",
        reply_markup=get_phone_keyboard(),
        parse_mode="HTML"
    )

@router.message(AppealForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    if not message.contact or not message.contact.phone_number:
        await message.answer("❌ Xatolik: kontakt topilmadi.", reply_markup=get_phone_keyboard())
        return
    phone = clean_phone(message.contact.phone_number)
    if not validate_phone_clean(phone):
        await message.answer(
            "❌ Noto'g'ri raqam. Qayta urinib ko'ring.",
            reply_markup=get_phone_keyboard()
        )
        return

    await state.update_data(phone=f"+{phone}")
    await state.set_state(AppealForm.full_name)
    await message.answer(
        f"✅ Raqam: <b>+{phone}</b>\n\n"
        "2-qadam: F.I.O. kiriting.",
        reply_markup=get_back_cancel_keyboard(),
        parse_mode="HTML"
    )

@router.message(AppealForm.full_name)
async def process_full_name(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xatolik: matn topilmadi.", reply_markup=get_back_cancel_keyboard())
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AppealForm.address)
    await message.answer("3-qadam: Yashash manzilini kiriting.", reply_markup=get_back_cancel_keyboard())

@router.message(AppealForm.address)
async def process_address(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xatolik: matn topilmadi.", reply_markup=get_back_cancel_keyboard())
        return
    await state.update_data(address=message.text.strip())
    await state.set_state(AppealForm.domkom)
    await message.answer("4-qadam: Uy MFI/OFI kompaniyasini kiriting.", reply_markup=get_back_cancel_keyboard())

@router.message(AppealForm.domkom)
async def process_domkom(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xatolik: matn topilmadi.", reply_markup=get_back_cancel_keyboard())
        return
    await state.update_data(domkom=message.text.strip())
    await state.set_state(AppealForm.text)
    await message.answer("5-qadam: Murojaatingizni tasvirlab bering.", reply_markup=get_back_cancel_keyboard())

@router.message(AppealForm.text)
async def process_text(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xatolik: matn topilmadi.", reply_markup=get_back_cancel_keyboard())
        return
    await state.update_data(text=message.text.strip())
    await state.set_state(AppealForm.media)
    await message.answer(
        "📸 6-qadam: Rasm/video qo'shing (ixtiyoriy)\n\n"
        "Fayllarni yuboring yoki <b>Keyingi</b> tugmasini bosing",
        reply_markup=get_media_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(media_files=[])

@router.message(AppealForm.media, F.photo | F.video)
async def process_media(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    media_files = data.get('media_files', [])

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    else:
        await message.answer("❌ Xatolik: fayl topilmadi.", reply_markup=get_media_keyboard())
        return

    file_info = await bot.get_file(file_id)
    if file_info.file_path is None:
        await message.answer("❌ Xatolik: fayl yo'li topilmadi.", reply_markup=get_media_keyboard())
        return
    file_ext = os.path.splitext(file_info.file_path)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(MEDIA_DIR, file_name)

    await bot.download_file(file_info.file_path, file_path)
    media_files.append({'path': file_path, 'type': file_type})
    await state.update_data(media_files=media_files)

    await message.answer(f"✅ Fayl #{len(media_files)} qo'shildi!\nYana yoki <b>Keyingi</b> tugmasini bosing", reply_markup=get_media_keyboard(), parse_mode="HTML")

@router.message(AppealForm.media, F.text == "Keyingi")
async def finish_media(message: Message, state: FSMContext):
    await state.set_state(AppealForm.preview)
    data = await state.get_data()
    preview_text = f"""
🌟 <b>MUROJAATNI TEKSHIRING</b> 🌟

📱 Telefon: <b>{data['phone']}</b>
👤 F.I.O.: <b>{data['full_name']}</b>
🏠 Manzil: <b>{data['address']}</b>
🏢 Uy MFI/OFI: <b>{data['domkom']}</b>
📝 Matn: <b>{data['text'][:100]}...</b>
📸 Fayllar: <b>{len(data.get('media_files', []))}</b>

Yuborish?
"""
    await message.answer(preview_text, parse_mode="HTML", reply_markup=get_preview_buttons(0))

@router.message(F.text == "🔙 Orqaga")
async def go_back(message: Message, state: FSMContext):
    current = await state.get_state()
    if current == AppealForm.full_name:
        await state.set_state(AppealForm.phone)
        await message.answer("📱 Raqamni qayta yuboring:", reply_markup=get_phone_keyboard())
    elif current == AppealForm.address:
        await state.set_state(AppealForm.full_name)
        await message.answer("2-qadam: F.I.O. kiriting.", reply_markup=get_back_cancel_keyboard())
    elif current == AppealForm.domkom:
        await state.set_state(AppealForm.address)
        await message.answer("3-qadam: Manzilni kiriting.", reply_markup=get_back_cancel_keyboard())
    elif current == AppealForm.text:
        await state.set_state(AppealForm.domkom)
        await message.answer("4-qadam: Uy MFI/OFI kiriting.", reply_markup=get_back_cancel_keyboard())
    elif current == AppealForm.media:
        await state.set_state(AppealForm.text)
        await message.answer("5-qadam: Murojaatni tasvirlang.", reply_markup=get_back_cancel_keyboard())
    elif current == AppealForm.preview:
        await state.set_state(AppealForm.media)
        await message.answer("📸 6-qadam: Rasm/video qo'shing (ixtiyoriy)\n\nFayllarni yuboring yoki <b>Keyingi</b> tugmasini bosing", reply_markup=get_media_keyboard(), parse_mode="HTML")

@router.message(F.text == "❌ Bekor qilish")
async def cancel_appeal(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return
    keyboard = get_main_admin_keyboard() if await is_admin(message.from_user.id) else get_main_user_keyboard()
    await message.answer("✖️ Yaratish bekor qilindi.", reply_markup=keyboard)

@router.callback_query(F.data.startswith("confirm_"))
async def confirm_appeal(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.from_user is None:
        await callback.answer("❌ Ошибка: пользователь не найден.")
        return
    data = await state.get_data()
    data['user_id'] = callback.from_user.id
    appeal_id = await create_appeal(data)
    for media in data.get('media_files', []):
        await add_media(appeal_id, media['path'], media['type'])

    if callback.message is None:
        await callback.answer("❌ Ошибка: сообщение не найдено.")
        return
    if callback.from_user is None:
        await callback.answer("❌ Foydalanuvchi topilmadi.")
        return
    keyboard = get_main_admin_keyboard() if await is_admin(callback.from_user.id) else get_main_user_keyboard()
    await callback.message.answer(
        f"🎉 <b>MUROJAAT YUBORILDI!</b>\n\n"
        f"Kuzatish uchun raqam: <b>№{appeal_id}</b>\n"
        f"Saqlab qoling! Biz siz bilan bog'lanamiz.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await notify_admins(bot, f"🆕 Новое обращение №{appeal_id} от {data['full_name']}")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "edit")
async def edit_appeal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AppealForm.phone)
    if callback.message is None:
        await callback.answer("❌ Xabar topilmadi.")
        return
    await callback.message.answer("✏️ Boshidan tahrirlaymiz:", reply_markup=get_phone_keyboard())
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def inline_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message is None or callback.from_user is None:
        await callback.answer("❌ Ma'lumotlar topilmadi.")
        return
    keyboard = get_main_admin_keyboard() if await is_admin(callback.from_user.id) else get_main_user_keyboard()
    await callback.message.answer("✖️ Bekor qilindi.", reply_markup=keyboard)
    await callback.answer()