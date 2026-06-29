# pyrefly: ignore [missing-import]
from aiogram import Router
# pyrefly: ignore [missing-import]
from aiogram.types import Message
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext

from database.db import db_one
from utils.helpers import get_lang
from utils.states import QuizStates
from keyboards.main_menu import main_menu_kb

router = Router()

@router.message()
async def fallback(msg: Message, state: FSMContext):
    cur = await state.get_state()
    if cur == QuizStates.answering_open:
        return  # Handled in quiz handler
    # pyrefly: ignore [missing-attribute]
    lang = await get_lang(msg.from_user.id)
    # pyrefly: ignore [missing-attribute]
    user = await db_one("SELECT registered FROM users WHERE user_id=?", (msg.from_user.id,))
    if user and user["registered"]:
        await msg.answer("❓ /help buyrug'i orqali imkoniyatlarni ko'ring.", reply_markup=main_menu_kb(lang))
