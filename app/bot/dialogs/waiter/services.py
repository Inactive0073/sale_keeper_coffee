import re

def normalize_phone_number(phone_number: str) -> str:
    """Приводит телефон к виду 7XXXXXXXXXX (только цифры, без +)"""
    digits_only = re.sub(r"\D", "", phone_number)  # Удаляем все нецифры
    if digits_only.startswith("8"):
        digits_only = "7" + digits_only[1:]
    elif digits_only.startswith("7"):
        digits_only = "7" + digits_only[1:]
    return digits_only