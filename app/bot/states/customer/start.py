from aiogram.fsm.state import State, StatesGroup


class CustomerSG(StatesGroup):
    # Приветствие
    start = State()
    name = State()
    surname = State()
    email = State()
    birthday = State()
    gender = State()
    thanks = State()

    # Меню
    menu = State()
    catalog = State()

    # Меню заказа
    catalog = State()
