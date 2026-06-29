import asyncio
from datetime import datetime
# pyrefly: ignore [missing-import]
from aiogram import Bot
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext
# pyrefly: ignore [missing-import]
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# pyrefly: ignore [missing-import]
from aiogram.enums import ParseMode
from database.db import db_exec
from utils.translations import tr

active_timers: dict[int, asyncio.Task] = {}

class TimerManager:
    @staticmethod
    def cancel_timer(user_id: int):
        if user_id in active_timers:
            active_timers[user_id].cancel()
            try:
                del active_timers[user_id]
            except KeyError:
                pass

    @staticmethod
    def start_timer(bot: Bot, user_id: int, state: FSMContext, lang: str, seconds: int):
        TimerManager.cancel_timer(user_id)
        task = asyncio.create_task(_timeout_task(bot, user_id, state, lang, seconds))
        active_timers[user_id] = task

async def _timeout_task(bot: Bot, user_id: int, state: FSMContext, lang: str, seconds: int):
    try:
        await asyncio.sleep(seconds)
        data = await state.get_data()
        q = data.get("current_q")
        if not q:
            return
        # Reset streak
        await db_exec("UPDATE users SET streak=0 WHERE user_id=?", (user_id,))
        await db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,0,?)",
                (user_id, q["id"], datetime.now().isoformat()))
        await state.update_data(current_q=None)
        try:
            await bot.edit_message_reply_markup(chat_id=data["chat_id"], message_id=data["q_msg_id"], reply_markup=None)
        except Exception:
            pass
        text = tr("time_up", lang, ans=q["answer"])
        if q.get("explanation"):
            text += f"\n\n{tr('fact_prefix', lang)}{q['explanation']}"
        next_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=tr("next_btn", lang), callback_data=f"next_{data.get('category','general')}"),
        ]])
        await bot.send_message(user_id, text, reply_markup=next_kb, parse_mode=ParseMode.HTML)
        await state.set_state(None)
    except asyncio.CancelledError:
        pass
    finally:
        if active_timers.get(user_id) == asyncio.current_task():
            try:
                del active_timers[user_id]
            except KeyError:
                pass
