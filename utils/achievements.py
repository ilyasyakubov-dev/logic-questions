from datetime import datetime
from aiogram import Bot
from database.db import db_one, db_exec
from utils.translations import tr

ACHIEVEMENTS = {
    "first_step":    {"uz": "🥇 Birinchi qadam",       "ru": "🥇 Первый шаг",         "en": "🥇 First Step",       "condition": lambda u: u["correct_cnt"] >= 1},
    "ten_correct":   {"uz": "🔟 10 to'g'ri javob",     "ru": "🔟 10 правильных",       "en": "🔟 10 Correct",       "condition": lambda u: u["correct_cnt"] >= 10},
    "fifty_correct": {"uz": "🌟 50 to'g'ri javob",     "ru": "🌟 50 правильных",       "en": "🌟 50 Correct",       "condition": lambda u: u["correct_cnt"] >= 50},
    "streak_5":      {"uz": "🔥 5 ta streak",           "ru": "🔥 Серия из 5",          "en": "🔥 5 Streak",         "condition": lambda u: u["best_streak"] >= 5},
    "streak_10":     {"uz": "🚀 10 ta streak",          "ru": "🚀 Серия из 10",         "en": "🚀 10 Streak",        "condition": lambda u: u["best_streak"] >= 10},
    "rich":          {"uz": "💎 1000 ball",             "ru": "💎 1000 очков",          "en": "💎 1000 Points",      "condition": lambda u: u["score"] >= 1000},
    "millionaire":   {"uz": "👑 10000 ball",            "ru": "👑 10000 очков",         "en": "👑 10000 Points",     "condition": lambda u: u["score"] >= 10000},
}

async def check_achievements(bot: Bot, user_id: int, lang: str):
    user = await db_one("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not user:
        return
    earned_rows = await db_exec("SELECT code FROM achievements WHERE user_id=?", (user_id,))
    earned = {r["code"] for r in earned_rows}
    for code, data in ACHIEVEMENTS.items():
        if code not in earned and data["condition"](user):
            await db_exec("INSERT OR IGNORE INTO achievements (user_id,code,earned_at) VALUES (?,?,?)",
                    (user_id, code, datetime.now().isoformat()))
            await bot.send_message(user_id, tr("new_achievement", lang, title=data[lang]))
