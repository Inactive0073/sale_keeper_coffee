from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from validators.url import url
from datetime import datetime as dt, timezone, timedelta


def parse_button(text: str) -> InlineKeyboardMarkup:
    """
    Парсит текст для создания Inline-клавиатуры с кнопками.

    Формат текста:
        Каждая строка — ряд кнопок. Элементы в строке разделены через "|".
        Каждая кнопка задается в формате: "Текст кнопки - URL".

    Пример:
        "Кнопка 1 - https://ya.ru | Кнопка 2 - https://google.com"
        "Кнопка 3 - https://ya.ru | Кнопка 4 - https://google.com"

    Args:
        text (str): Входной текст с описанием кнопок.

    Returns:
        InlineKeyboardMarkup: Объект клавиатуры с кнопками.

    Raises:
        ValueError:
            - Если формат строки кнопки некорректен (не разделено на "Текст - URL").
            - Если URL не проходит валидацию.
    """
    builder = InlineKeyboardBuilder()

    for row in text.strip().split("\n"):
        row_buttons = []
        for el in row.split("|"):
            parts = [p.strip() for p in el.split(" - ")]

            if len(parts) != 2:
                raise ValueError(
                    f"Некорректный формат кнопки.\n"
                    f"Образец ссылки: Example link - https://ya.ru\n"
                    f"Получено: {''.join(parts)}\n"
                )
            name, link = parts
            if not url(link):
                raise ValueError(f"Ошибка в процессе валидации ссылки: {link}")

            row_buttons.append(InlineKeyboardButton(text=name, url=link))

        builder.row(*row_buttons)

    return builder.as_markup()


def parse_time(time: str):
    """
    Парсит строку времени в формате HH, HHMM, HHMMDD
    и возвращает datetime с замененными значениями.

    Args:
        time (str): Строка времени (только цифры)

    Returns:
        datetime: Объект datetime

    Raises:
        ValueError: При неверном формате или некорректных значениях
    """
    FIXED_MSK = timezone(timedelta(hours=3))
    while " " in time.strip():
        time = time.replace(" ", "")

    if not all((char.isdigit() for char in time)):
        raise ValueError

    date = dt.now()

    if len(time) == 2:
        hour = int(time)
        date = date.replace(hour=hour, minute=0)

    elif len(time) <= 4:
        hour = int(str(time[:2]))
        minute = int(str(time[2:]))
        date = date.replace(hour=hour, minute=minute)

    elif len(time) == 8:
        hour, minute, day, month = [
            int(str(time[i : i + 2])) for i in range(0, len(time), 2)
        ]
        date = date.replace(hour=hour, minute=minute, day=day, month=month)

    else:
        raise ValueError

    date = date.replace(second=0, microsecond=0, tzinfo=FIXED_MSK)
    return date


def get_delay(post_time: dt) -> float:
    """
    Вычисляет задержку в секундах между текущим моментом и указанным временем.

    Args:
        post_time (datetime): Целевое время (с учетом часового пояса)

    Returns:
        float: Задержка в секундах (положительное число)

    Raises:
        ValueError: Если post_time находится в прошлом
    """
    now = dt.now(post_time.tzinfo)
    delay = (post_time - now).total_seconds()

    if delay <= 0:
        raise ValueError("Время публикации должно быть в будущем")

    return delay
