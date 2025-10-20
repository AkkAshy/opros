import re

def validate_phone(phone: str) -> bool:
    pattern = r'^(\+998|998)?[\s\-]?\(?9[0-9]\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$'
    return bool(re.match(pattern, phone))

def validate_phone_clean(phone: str) -> bool:
    """Валидация очищенного номера (только цифры)"""
    pattern = r'^9989\d{8}$'
    return bool(re.match(pattern, phone))

def clean_phone(phone: str) -> str:
    return re.sub(r'\D', '', phone)