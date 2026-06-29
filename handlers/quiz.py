import random
from datetime import datetime
# pyrefly: ignore [missing-import]
from aiogram import Router, F, Bot
# pyrefly: ignore [missing-import]
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
# pyrefly: ignore [missing-import]
from aiogram.enums import ParseMode
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext

from database.db import db_exec, db_one
from utils.translations import tr, T
from utils.states import QuizStates
from utils.helpers import add_score, get_lang
from utils.timers import TimerManager
from utils.achievements import check_achievements
from keyboards.inline import category_inline_kb

router = Router()

async def ensure_registered(msg: Message) -> dict:
    # pyrefly: ignore [missing-attribute]
    user = await db_one("SELECT * FROM users WHERE user_id=? AND registered=1", (msg.from_user.id,))
    if not user:
        await msg.answer("❗ Avval /start buyrug'ini yuboring va ro'yxatdan o'ting.")
    # pyrefly: ignore [bad-return]
    return user

@router.message(F.text.func(lambda t: any(t == T["btn_questions"][l] for l in ("uz","ru","en"))))
async def menu_questions(msg: Message, state: FSMContext):
    user = await ensure_registered(msg)
    if not user:
        return
    await state.clear()
    lang = user["lang"]
    await msg.answer(tr("choose_category", lang), reply_markup=category_inline_kb(lang))

@router.callback_query(F.data.startswith("cat_"))
async def cb_category(call: CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    # pyrefly: ignore [unsupported-operation]
    category = call.data[4:]   # "math" / "history" / "science" / "general"
    await state.update_data(category=category)
    # pyrefly: ignore [missing-attribute]
    await call.message.edit_reply_markup()
    # pyrefly: ignore [bad-argument-type]
    await send_question(call.message, call.from_user.id, state, lang, category)
    await call.answer()

async def send_question(msg: Message, user_id: int, state: FSMContext, lang: str, category: str):
    # Cancel existing timer
    TimerManager.cancel_timer(user_id)

    # Pick random question not recently answered (last 20)
    recent_rows = await db_exec(
        "SELECT question_id FROM answered WHERE user_id=? ORDER BY answered_at DESC LIMIT 20",
        (user_id,)
    )
    recent = [r["question_id"] for r in recent_rows]
    placeholders = ",".join("?" * len(recent)) if recent else "0"
    q = await db_one(
        f"SELECT * FROM questions WHERE category=? AND lang=? AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1",
        (category, lang, *recent)
    )
    if not q:
        # Allow repeats if pool is small
        q = await db_one("SELECT * FROM questions WHERE category=? AND lang=? ORDER BY RANDOM() LIMIT 1",
                   (category, lang))
    if not q:
        await msg.answer(tr("no_questions", lang))
        return

    diff_stars = "⭐" * q["difficulty"]
    header = f"<b>#{q['id']} | {diff_stars}</b>\n\n❓ {q['question']}\n"
    await state.update_data(current_q=dict(q), category=category, hint_used=False, reveal_used=False, revealed_word="")

    if q["q_type"] == "choice":
        options = {"A": q["option_a"], "B": q["option_b"], "C": q["option_c"]}
        opts_text = "\n".join(f"  <b>{k})</b> {v}" for k, v in options.items())
        text = header + opts_text + f"\n\n⏱ <i>30 soniya</i>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"A) {q['option_a']}", callback_data="ans_A"),
             InlineKeyboardButton(text=f"B) {q['option_b']}", callback_data="ans_B"),
             InlineKeyboardButton(text=f"C) {q['option_c']}", callback_data="ans_C")],
            [InlineKeyboardButton(text=tr("hint_btn", lang), callback_data="hint"),
             InlineKeyboardButton(text=tr("skip_btn", lang), callback_data="skip_q")],
        ])
        sent = await msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        text = header + "\n" + tr("open_answer", lang) + f"\n\n⏱ <i>30 soniya</i>"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=tr("reveal_btn", lang), callback_data="reveal"),
            InlineKeyboardButton(text=tr("skip_btn", lang), callback_data="skip_q"),
        ]])
        sent = await msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await state.set_state(QuizStates.answering_open)

    await state.update_data(q_msg_id=sent.message_id, chat_id=sent.chat.id)

    # Start 30-second countdown timer using TimerManager
    # pyrefly: ignore [bad-argument-type]
    TimerManager.start_timer(msg.bot, user_id, state, lang, 30)

@router.callback_query(F.data.startswith("ans_"))
async def cb_answer_choice(call: CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    if not q:
        await call.answer("❗")
        return

    # Cancel timer
    TimerManager.cancel_timer(call.from_user.id)

    # pyrefly: ignore [unsupported-operation]
    chosen = call.data[4:]  # A/B/C
    correct = q["answer"]   # A/B/C
    user = await db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
    is_correct = chosen == correct

    # Base points by difficulty
    base_pts = {1: 10, 2: 20, 3: 35}.get(q["difficulty"], 10)
    pts_earned = 0

    await db_exec("UPDATE users SET wrong_cnt=wrong_cnt+1 WHERE user_id=?", (call.from_user.id,))
    await db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,?,?)",
            (call.from_user.id, q["id"], int(is_correct), datetime.now().isoformat()))

    if is_correct:
        await db_exec("UPDATE users SET correct_cnt=correct_cnt+1, wrong_cnt=wrong_cnt-1, streak=streak+1 WHERE user_id=?",
                (call.from_user.id,))
        user_upd = await db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
        # pyrefly: ignore [unsupported-operation]
        streak = user_upd["streak"]
        # Update best streak
        # pyrefly: ignore [unsupported-operation]
        if streak > user_upd["best_streak"]:
            await db_exec("UPDATE users SET best_streak=? WHERE user_id=?", (streak, call.from_user.id))
        pts_earned = base_pts
        await add_score(call.from_user.id, pts_earned)
        result_text = tr("correct", lang, pts=pts_earned)
        # Streak bonus every 5
        if streak > 0 and streak % 5 == 0:
            bonus = streak * 2
            await add_score(call.from_user.id, bonus)
            result_text += "\n" + tr("streak_bonus", lang, streak=streak, bonus=bonus)
    else:
        await db_exec("UPDATE users SET streak=0 WHERE user_id=?", (call.from_user.id,))
        ans_text = q["option_" + correct.lower()] if correct in ("A","B","C") else correct
        result_text = tr("wrong", lang, ans=f"{correct}) {ans_text}")

    if q.get("explanation"):
        result_text += f"\n\n{tr('fact_prefix', lang)}{q['explanation']}"

    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("next_btn", lang), callback_data=f"next_{data.get('category','general')}"),
    ]])

    try:
        # pyrefly: ignore [missing-attribute]
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    # pyrefly: ignore [missing-attribute]
    await call.message.answer(result_text, reply_markup=next_kb, parse_mode=ParseMode.HTML)
    await state.update_data(current_q=None)
    await state.set_state(None)
    # pyrefly: ignore [bad-argument-type]
    await check_achievements(call.bot, call.from_user.id, lang)
    await call.answer()

@router.message(QuizStates.answering_open)
async def handle_open_answer(msg: Message, state: FSMContext):
    # pyrefly: ignore [missing-attribute]
    lang = await get_lang(msg.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    if not q:
        return

    # Cancel timer
    # pyrefly: ignore [missing-attribute]
    TimerManager.cancel_timer(msg.from_user.id)

    # pyrefly: ignore [missing-attribute]
    user_ans = msg.text.strip().lower()
    correct_ans = q["answer"].strip().lower()
    is_correct = user_ans == correct_ans

    base_pts = {1: 20, 2: 35, 3: 50}.get(q["difficulty"], 20)  # Open = more points

    await db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,?,?)",
            # pyrefly: ignore [missing-attribute]
            (msg.from_user.id, q["id"], int(is_correct), datetime.now().isoformat()))

    if is_correct:
        # pyrefly: ignore [missing-attribute]
        await db_exec("UPDATE users SET correct_cnt=correct_cnt+1, streak=streak+1 WHERE user_id=?", (msg.from_user.id,))
        # pyrefly: ignore [missing-attribute]
        user_upd = await db_one("SELECT * FROM users WHERE user_id=?", (msg.from_user.id,))
        # pyrefly: ignore [unsupported-operation]
        streak = user_upd["streak"]
        # pyrefly: ignore [unsupported-operation]
        if streak > user_upd["best_streak"]:
            # pyrefly: ignore [missing-attribute]
            await db_exec("UPDATE users SET best_streak=? WHERE user_id=?", (streak, msg.from_user.id))
        # pyrefly: ignore [missing-attribute]
        await add_score(msg.from_user.id, base_pts)
        result_text = tr("correct", lang, pts=base_pts)
        if streak > 0 and streak % 5 == 0:
            bonus = streak * 2
            # pyrefly: ignore [missing-attribute]
            await add_score(msg.from_user.id, bonus)
            result_text += "\n" + tr("streak_bonus", lang, streak=streak, bonus=bonus)
    else:
        # pyrefly: ignore [missing-attribute]
        await db_exec("UPDATE users SET wrong_cnt=wrong_cnt+1, streak=0 WHERE user_id=?", (msg.from_user.id,))
        result_text = tr("wrong", lang, ans=q["answer"])

    if q.get("explanation"):
        result_text += f"\n\n{tr('fact_prefix', lang)}{q['explanation']}"

    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("next_btn", lang), callback_data=f"next_{data.get('category','general')}"),
    ]])
    await msg.answer(result_text, reply_markup=next_kb, parse_mode=ParseMode.HTML)
    await state.update_data(current_q=None)
    await state.set_state(None)
    # pyrefly: ignore [bad-argument-type, missing-attribute]
    await check_achievements(msg.bot, msg.from_user.id, lang)

@router.callback_query(F.data == "hint")
async def cb_hint(call: CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    user = await db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
    if data.get("hint_used"):
        await call.answer("💡 Yordam allaqachon ishlatildi!", show_alert=True)
        return
    # pyrefly: ignore [unsupported-operation]
    if user["score"] < 50:
        # pyrefly: ignore [unsupported-operation]
        await call.answer(tr("not_enough_pts", lang, pts=user["score"], need=50), show_alert=True)
        return
    # Pick a wrong option
    # pyrefly: ignore [unsupported-operation]
    correct = q["answer"]
    wrong_opts = [x for x in ["A","B","C"] if x != correct]
    eliminated = random.choice(wrong_opts)
    await add_score(call.from_user.id, -50)
    await state.update_data(hint_used=True)
    await call.answer(tr("hint_used", lang, opt=eliminated), show_alert=True)

@router.callback_query(F.data == "reveal")
async def cb_reveal(call: CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    user = await db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
    # pyrefly: ignore [unsupported-operation]
    if user["score"] < 25:
        # pyrefly: ignore [unsupported-operation]
        await call.answer(tr("not_enough_pts", lang, pts=user["score"], need=25), show_alert=True)
        return
    # pyrefly: ignore [unsupported-operation]
    answer = q["answer"].upper()
    revealed_str = data.get("revealed_word", "_" * len(answer))
    hidden_positions = [i for i, c in enumerate(revealed_str) if c == "_"]
    if not hidden_positions:
        await call.answer("Barcha harflar ochilgan!", show_alert=True)
        return
    idx = random.choice(hidden_positions)
    new_revealed = list(revealed_str)
    new_revealed[idx] = answer[idx]
    new_word = "".join(new_revealed)
    await add_score(call.from_user.id, -25)
    await state.update_data(revealed_word=new_word)
    display = " ".join(new_word)
    await call.answer(tr("reveal_used", lang, word=display), show_alert=True)

@router.callback_query(F.data == "skip_q")
async def cb_skip(call: CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    data = await state.get_data()
    TimerManager.cancel_timer(call.from_user.id)
    q = data.get("current_q")
    if q:
        await db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,0,?)",
                (call.from_user.id, q["id"], datetime.now().isoformat()))
        await db_exec("UPDATE users SET streak=0 WHERE user_id=?", (call.from_user.id,))
    category = data.get("category", "general")
    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("next_btn", lang), callback_data=f"next_{category}"),
    ]])
    try:
        # pyrefly: ignore [missing-attribute]
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    # pyrefly: ignore [missing-attribute]
    await call.message.answer("⏭ O'tkazib yuborildi.", reply_markup=next_kb)
    await state.update_data(current_q=None)
    await state.set_state(None)
    await call.answer()

@router.callback_query(F.data.startswith("next_"))
async def cb_next(call: CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    # pyrefly: ignore [unsupported-operation]
    category = call.data[5:]
    await state.update_data(category=category)
    # pyrefly: ignore [missing-attribute]
    await call.message.edit_reply_markup()
    # pyrefly: ignore [bad-argument-type]
    await send_question(call.message, call.from_user.id, state, lang, category)
    await call.answer()
