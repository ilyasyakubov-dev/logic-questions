from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from database.db import db_one, db_exec
from utils.translations import tr
from utils.states import RegStates
from keyboards.main_menu import main_menu_kb
from keyboards.inline import lang_inline_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    user = await db_one("SELECT * FROM users WHERE user_id=?", (msg.from_user.id,))
    if user and user["registered"]:
        lang = user["lang"]
        await msg.answer(tr("reg_done", lang, name=user["first_name"]).split("\n\n")[0] + "\n\n👋",
                         reply_markup=main_menu_kb(lang))
        return
    # First time — choose language
    await msg.answer(tr("choose_lang", "uz"), reply_markup=lang_inline_kb())

@router.callback_query(F.data.startswith("lang_"))
async def cb_lang(call: CallbackQuery, state: FSMContext):
    lang = call.data.split("_")[1]
    uid = call.from_user.id
    user = await db_one("SELECT * FROM users WHERE user_id=?", (uid,))
    if not user:
        await db_exec("INSERT OR IGNORE INTO users (user_id,username,lang,joined_at) VALUES (?,?,?,?)",
                (uid, call.from_user.username, lang, datetime.now().isoformat()))
    else:
        await db_exec("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
        if user["registered"]:
            await call.message.edit_reply_markup()
            await call.message.answer("✅", reply_markup=main_menu_kb(lang))
            await call.answer()
            return
    await state.update_data(lang=lang)
    await call.message.edit_reply_markup()
    await call.message.answer(tr("welcome_reg", lang), parse_mode=ParseMode.HTML)
    await state.set_state(RegStates.waiting_first)
    await call.answer()
