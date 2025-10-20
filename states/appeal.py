from aiogram.fsm.state import State, StatesGroup

class AppealForm(StatesGroup):
    phone = State()         # Шаг 1: Телефон
    full_name = State()     # Шаг 2: ФИО
    address = State()       # Шаг 3: Адрес
    domkom = State()        # Шаг 4: Домком
    text = State()          # Шаг 5: Текст
    media = State()         # Шаг 6: Медиа (опционально)
    preview = State()       # Предпросмотр и подтверждение

class AdminForm(StatesGroup):
    waiting_for_user_id = State()  # Ожидание ID пользователя для добавления в админы
    waiting_for_comment = State()  # Ожидание комментария к обращению