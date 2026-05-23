from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    email = State()
    password = State()
    full_name = State()
    passport = State()
    birth = State()
    citizenship = State()
    serbia_status = State()
    serbia_id = State()
    date_from = State()
    date_to = State()
    weekdays = State()
    confirm = State()
