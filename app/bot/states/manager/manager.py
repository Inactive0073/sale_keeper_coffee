from aiogram.fsm.state import State, StatesGroup


class ManagerSG(StatesGroup):
    start = State()
    demo = State()  # Представление возможностей бота
