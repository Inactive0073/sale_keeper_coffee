from aiogram.fsm.state import State, StatesGroup


class ContentSG(StatesGroup):
    start = State()
    bot = State()
    channel = State()
    today_info = State()
    process_selected = State()
