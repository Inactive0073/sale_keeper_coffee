from aiogram.fsm.state import State, StatesGroup


class AdminSG(StatesGroup):
    start = State()

    reports = State()
    report_users = State()
    report_bonuses = State()
    report_posts = State()

    ban_menu = State()
    ban = State()
    unban = State()

    team = State()
    selecting_role = State()
    invite = State()

    selecting_employee = State()
    kick = State()
