# pyrefly: ignore [missing-import]
from aiogram import Router, F
# pyrefly: ignore [missing-import]
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
# pyrefly: ignore [missing-import]
from aiogram.enums import ParseMode
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext

from database.db import db_exec
from utils.translations import tr
from utils.states import RegStates
from utils.helpers import add_score
from utils.achievements import check_achievements
from keyboards.main_menu import main_menu_kb

router = Router()

@router.message(RegStates.waiting_first)
async def reg_first(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    # pyrefly: ignore [missing-attribute]
    await state.update_data(first_name=msg.text.strip())
    await msg.answer(tr("enter_last", lang), parse_mode=ParseMode.HTML)
    await state.set_state(RegStates.waiting_last)

@router.message(RegStates.waiting_last)
async def reg_last(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    # pyrefly: ignore [missing-attribute]
    await state.update_data(last_name=msg.text.strip())
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr("send_phone_btn", lang), request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await msg.answer(tr("enter_phone", lang), reply_markup=kb, parse_mode=ParseMode.HTML)
    await state.set_state(RegStates.waiting_phone)

@router.message(RegStates.waiting_phone, F.contact | F.text)
async def reg_phone(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    if not msg.text and not msg.contact:
        await msg.answer("❌ Telefon raqamini yuboring.")
        return
    # pyrefly: ignore [missing-attribute]
    phone = msg.contact.phone_number if msg.contact else msg.text.strip()
    # pyrefly: ignore [missing-attribute]
    uid = msg.from_user.id
    await db_exec("""UPDATE users SET first_name=?,last_name=?,phone=?,registered=1,score=200
               WHERE user_id=?""",
            (data["first_name"], data["last_name"], phone, uid))
    await add_score(uid, 0)  # ensure weekly row
    await state.clear()
    await msg.answer(
        tr("reg_done", lang, name=data["first_name"]),
        reply_markup=main_menu_kb(lang),
        parse_mode=ParseMode.HTML,
    )
    # First achievement
    # pyrefly: ignore [bad-argument-type]
    await check_achievements(msg.bot, uid, lang)
