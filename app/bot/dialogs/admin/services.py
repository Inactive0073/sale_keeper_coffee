from app.bot.db.models import User


def parse_username_or_id_data(data: str) -> str:
    if data.startswith("@"):
        return data.replace("@", "")
    if data.isdigit():
        return data
    raise ValueError(
        "Неподходящий формат сообщения для добавления нового юзера в команду. Допустимый формат 665323 или @username"
    )


def get_telegram_id(user: User):
    return user.telegram_id
