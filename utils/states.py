# pyrefly: ignore [missing-import]
from aiogram.fsm.state import State, StatesGroup

class RegStates(StatesGroup):
    waiting_first = State()
    waiting_last = State()
    waiting_phone = State()

class QuizStates(StatesGroup):
    answering_open = State()
