from aiogram.fsm.state import State, StatesGroup


class WaiterSG(StatesGroup):
    start = State()
    processing = State()
    adding = State()
    subtracting = State()
    instruction = State()
