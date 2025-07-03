from aiogram.fsm.state import State, StatesGroup


class SettingsSG(StatesGroup):
    start = State()
    timezone = State()
    support = State()
