from datetime import date, datetime, timedelta
# pyrefly: ignore [missing-import]
from aiogram import Router, F
# pyrefly: ignore [missing-import]
from aiogram.types import Message
# pyrefly: ignore [missing-import]
from aiogram.enums import ParseMode

from database.db import db_exec, db_one
from utils.translations import tr, T
from utils.helpers import week_start, add_score
from utils.achievements import ACHIEVEMENTS, check_achievements
from keyboards.inline import lang_inline_kb
from keyboards.main_menu import main_menu_kb
from handlers.quiz import ensure_registered

router = Router()

medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

@router.message(F.text.func(lambda t: any(t == T["btn_rating"][l] for l in ("uz","ru","en"))))
async def menu_rating(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    rows = await db_exec("SELECT first_name,last_name,score FROM users WHERE registered=1 ORDER BY score DESC LIMIT 5")
    if not rows:
        await msg.answer("Hali ma'lumot yo'q.")
        return
    text = tr("top_header", lang)
    for i, r in enumerate(rows):
        text += f"{medal[i]} <b>{r['first_name']} {r['last_name']}</b> — {r['score']} ball\n"
    await msg.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text.func(lambda t: any(t == T["btn_weekly"][l] for l in ("uz","ru","en"))))
async def menu_weekly(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    ws = week_start()
    rows = await db_exec("""
        SELECT u.first_name, u.last_name, w.score
        FROM weekly_scores w JOIN users u ON w.user_id=u.user_id
        WHERE w.week_start=? ORDER BY w.score DESC LIMIT 5
    """, (ws,))
    if not rows:
        await msg.answer("Bu hafta hali ma'lumot yo'q.")
        return
    text = tr("weekly_header", lang)
    for i, r in enumerate(rows):
        text += f"{medal[i]} <b>{r['first_name']} {r['last_name']}</b> — {r['score']} ball\n"
    await msg.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text.func(lambda t: any(t == T["btn_my_score"][l] for l in ("uz","ru","en"))))
async def menu_my_score(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    total = user["correct_cnt"] + user["wrong_cnt"]
    pct = round(user["correct_cnt"] / total * 100) if total else 0
    await msg.answer(
        tr("my_score_text", lang,
           name=f"{user['first_name']} {user['last_name']}",
           score=user["score"],
           correct=user["correct_cnt"],
           wrong=user["wrong_cnt"],
           pct=pct,
           best_streak=user["best_streak"],
           total=total),
        parse_mode=ParseMode.HTML,
    )

@router.message(F.text.func(lambda t: any(t == T["btn_achievements"][l] for l in ("uz","ru","en"))))
async def menu_achievements(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    # pyrefly: ignore [missing-attribute]
    earned = await db_exec("SELECT code,earned_at FROM achievements WHERE user_id=? ORDER BY earned_at", (msg.from_user.id,))
    if not earned:
        await msg.answer(tr("achievements_header", lang) + tr("no_achievements", lang), parse_mode=ParseMode.HTML)
        return
    text = tr("achievements_header", lang)
    for r in earned:
        title = ACHIEVEMENTS.get(r["code"], {}).get(lang, r["code"])
        date_str = r["earned_at"][:10]
        text += f"{title}  <i>({date_str})</i>\n"
    earned_codes = {r["code"] for r in earned}
    locked = [ACHIEVEMENTS[c][lang] for c in ACHIEVEMENTS if c not in earned_codes]
    if locked:
        # pyrefly: ignore [no-matching-overload]
        text += "\n🔒 <i>" + ", ".join(locked) + "</i>"
    await msg.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text.func(lambda t: any(t == T["btn_daily_bonus"][l] for l in ("uz","ru","en"))))
async def menu_daily_bonus(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    today = date.today().isoformat()
    if user["last_daily"] == today:
        next_time = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
        remaining = next_time - datetime.now()
        h, m = divmod(int(remaining.total_seconds() // 60), 60)
        await msg.answer(tr("daily_bonus_already", lang, time=f"{h}soat {m}daqiqa"), parse_mode=ParseMode.HTML)
        return
    # pyrefly: ignore [missing-attribute]
    await db_exec("UPDATE users SET last_daily=? WHERE user_id=?", (today, msg.from_user.id))
    # pyrefly: ignore [missing-attribute]
    await add_score(msg.from_user.id, 100)
    await msg.answer(tr("daily_bonus_received", lang), parse_mode=ParseMode.HTML)
    # pyrefly: ignore [bad-argument-type, missing-attribute]
    await check_achievements(msg.bot, msg.from_user.id, lang)

@router.message(F.text.func(lambda t: any(t == T["btn_change_lang"][l] for l in ("uz","ru","en"))))
async def menu_change_lang(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    await msg.answer(tr("choose_lang", user["lang"]), reply_markup=lang_inline_kb())
