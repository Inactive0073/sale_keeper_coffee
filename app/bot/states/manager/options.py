from aiogram.fsm.state import State, StatesGroup


class OptionsSG(StatesGroup):
    cancel = State()  # для отмены и шага назад
