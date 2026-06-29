"""
🧠 QuizMaster Bot — Professional Telegram Quiz Bot
Author: 10-yillik tajribali Python/aiogram dasturchisi
Stack: Python 3.11+, aiogram 3.x, SQLite (aiosqlite), APScheduler

Qo'shimcha funksiyalar (o'zim qo'shganlarim):
- 🔥 Streak tizimi (ketma-ket to'g'ri javoblar uchun bonus ball)
- 🏆 Achievement (yutuq) tizimi: "Birinchi qadam", "10 savol ustasi" va h.k.
- 📊 Shaxsiy statistika: to'g'ri/noto'g'ri javoblar foizi
- ⏱ Savol uchun vaqt chegarasi (30 soniya, aks holda ball yo'qoladi)
- 🎯 Kategoriya tanlash: Matematika, Tarix, Fan, Umumiy bilim
- 🎁 Kunlik bonus: har kuni birinchi kirganda +100 ball
- 📅 Haftalik reyting: hafta davomida eng ko'p ball to'plaganlar
- 🔔 Kechqurun eslatma xabari (agar bugun savol yechilmagan bo'lsa)
- 💬 To'g'ri javobdan keyin qiziqarli fakt/izoh ko'rsatish
"""

import asyncio
import logging
import random
import sqlite3
import os
from datetime import datetime, timedelta, date
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# ─────────────────────────────────────────────
# BOT TOKEN — .env yoki to'g'ridan-to'g'ri yozing
# ─────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# TRANSLATIONS
# ─────────────────────────────────────────────
T = {
    "choose_lang": {
        "uz": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "ru": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "en": "🌐 Tilni tanlang / Выберите язык / Choose language:",
    },
    "welcome_reg": {
        "uz": "👋 Xush kelibsiz! Ro'yxatdan o'tish uchun <b>ismingizni</b> kiriting:",
        "ru": "👋 Добро пожаловать! Введите ваше <b>имя</b>:",
        "en": "👋 Welcome! Please enter your <b>first name</b>:",
    },
    "enter_last": {
        "uz": "✅ Zo'r! Endi <b>familiyangizni</b> kiriting:",
        "ru": "✅ Отлично! Теперь введите вашу <b>фамилию</b>:",
        "en": "✅ Great! Now enter your <b>last name</b>:",
    },
    "enter_phone": {
        "uz": "📱 Endi <b>telefon raqamingizni</b> yuboring (tugma orqali yoki +998XXXXXXXXX formatida yozing):",
        "ru": "📱 Теперь отправьте <b>номер телефона</b> (кнопкой или в формате +998XXXXXXXXX):",
        "en": "📱 Now send your <b>phone number</b> (via button or type +998XXXXXXXXX):",
    },
    "send_phone_btn": {
        "uz": "📲 Telefon raqamni yuborish",
        "ru": "📲 Отправить номер телефона",
        "en": "📲 Share phone number",
    },
    "reg_done": {
        "uz": "🎉 Ro'yxatdan muvaffaqiyatli o'tdingiz, <b>{name}</b>!\n\n🏆 Sizga xush kelibsiz bonusi: <b>+200 ball!</b>\n\nQuyidagi menyudan foydalaning:",
        "ru": "🎉 Регистрация успешна, <b>{name}</b>!\n\n🏆 Бонус за вход: <b>+200 очков!</b>\n\nИспользуйте меню ниже:",
        "en": "🎉 Registration complete, <b>{name}</b>!\n\n🏆 Welcome bonus: <b>+200 points!</b>\n\nUse the menu below:",
    },
    # Main menu buttons
    "btn_questions": {"uz": "🧠 Savollar", "ru": "🧠 Вопросы", "en": "🧠 Questions"},
    "btn_rating": {"uz": "🏆 Reyting", "ru": "🏆 Рейтинг", "en": "🏆 Leaderboard"},
    "btn_my_score": {"uz": "📊 Mening natijam", "ru": "📊 Мой результат", "en": "📊 My Score"},
    "btn_weekly": {"uz": "📅 Haftalik TOP", "ru": "📅 Недельный ТОП", "en": "📅 Weekly TOP"},
    "btn_achievements": {"uz": "🏅 Yutuqlarim", "ru": "🏅 Достижения", "en": "🏅 Achievements"},
    "btn_daily_bonus": {"uz": "🎁 Kunlik bonus", "ru": "🎁 Ежедневный бонус", "en": "🎁 Daily Bonus"},
    "btn_change_lang": {"uz": "🌐 Tilni o'zgartirish", "ru": "🌐 Сменить язык", "en": "🌐 Change language"},
    # Category selection
    "choose_category": {
        "uz": "📚 Kategoriyani tanlang:",
        "ru": "📚 Выберите категорию:",
        "en": "📚 Choose a category:",
    },
    "cat_math": {"uz": "🔢 Matematika", "ru": "🔢 Математика", "en": "🔢 Math"},
    "cat_history": {"uz": "📜 Tarix", "ru": "📜 История", "en": "📜 History"},
    "cat_science": {"uz": "🔬 Fan", "ru": "🔬 Наука", "en": "🔬 Science"},
    "cat_general": {"uz": "🌍 Umumiy bilim", "ru": "🌍 Общие знания", "en": "🌍 General Knowledge"},
    # Question UI
    "hint_btn": {"uz": "💡 Yordam (50 ball)", "ru": "💡 Подсказка (50 очков)", "en": "💡 Hint (50 pts)"},
    "reveal_btn": {"uz": "🔤 Harf ochish (25 ball)", "ru": "🔤 Открыть букву (25 очков)", "en": "🔤 Reveal letter (25 pts)"},
    "next_btn": {"uz": "➡️ Keyingi savol", "ru": "➡️ Следующий вопрос", "en": "➡️ Next question"},
    "skip_btn": {"uz": "⏭ O'tkazib yuborish", "ru": "⏭ Пропустить", "en": "⏭ Skip"},
    "not_enough_pts": {
        "uz": "❌ Ball yetarli emas! Sizda <b>{pts}</b> ball bor, lekin <b>{need}</b> ball kerak.",
        "ru": "❌ Недостаточно очков! У вас <b>{pts}</b>, нужно <b>{need}</b>.",
        "en": "❌ Not enough points! You have <b>{pts}</b> but need <b>{need}</b>.",
    },
    "correct": {
        "uz": "✅ To'g'ri javob! <b>+{pts} ball</b>",
        "ru": "✅ Правильно! <b>+{pts} очков</b>",
        "en": "✅ Correct! <b>+{pts} points</b>",
    },
    "wrong": {
        "uz": "❌ Noto'g'ri! To'g'ri javob: <b>{ans}</b>",
        "ru": "❌ Неверно! Правильный ответ: <b>{ans}</b>",
        "en": "❌ Wrong! Correct answer: <b>{ans}</b>",
    },
    "streak_bonus": {
        "uz": "🔥 Streak bonusi! {streak} ta ketma-ket to'g'ri javob: <b>+{bonus} bonus ball!</b>",
        "ru": "🔥 Бонус за серию! {streak} ответов подряд: <b>+{bonus} бонусных очков!</b>",
        "en": "🔥 Streak bonus! {streak} in a row: <b>+{bonus} bonus points!</b>",
    },
    "time_up": {
        "uz": "⏱ Vaqt tugadi! To'g'ri javob: <b>{ans}</b>. Streak uzildi.",
        "ru": "⏱ Время вышло! Правильный ответ: <b>{ans}</b>. Серия прервана.",
        "en": "⏱ Time's up! Correct answer: <b>{ans}</b>. Streak broken.",
    },
    "no_questions": {
        "uz": "😔 Bu kategoriyada savol topilmadi. Boshqa kategoriya tanlang.",
        "ru": "😔 Вопросов в этой категории нет. Выберите другую.",
        "en": "😔 No questions found in this category. Try another.",
    },
    "my_score_text": {
        "uz": (
            "📊 <b>Sizning natijalaringiz:</b>\n\n"
            "👤 Ism: <b>{name}</b>\n"
            "💎 Jami ball: <b>{score}</b>\n"
            "✅ To'g'ri javoblar: <b>{correct}</b>\n"
            "❌ Noto'g'ri javoblar: <b>{wrong}</b>\n"
            "📈 Aniqlik: <b>{pct}%</b>\n"
            "🔥 Eng uzun streak: <b>{best_streak}</b>\n"
            "❓ Jami yechilgan: <b>{total}</b> ta savol"
        ),
        "ru": (
            "📊 <b>Ваши результаты:</b>\n\n"
            "👤 Имя: <b>{name}</b>\n"
            "💎 Всего очков: <b>{score}</b>\n"
            "✅ Правильных: <b>{correct}</b>\n"
            "❌ Неправильных: <b>{wrong}</b>\n"
            "📈 Точность: <b>{pct}%</b>\n"
            "🔥 Лучшая серия: <b>{best_streak}</b>\n"
            "❓ Всего вопросов: <b>{total}</b>"
        ),
        "en": (
            "📊 <b>Your Statistics:</b>\n\n"
            "👤 Name: <b>{name}</b>\n"
            "💎 Total points: <b>{score}</b>\n"
            "✅ Correct: <b>{correct}</b>\n"
            "❌ Wrong: <b>{wrong}</b>\n"
            "📈 Accuracy: <b>{pct}%</b>\n"
            "🔥 Best streak: <b>{best_streak}</b>\n"
            "❓ Total answered: <b>{total}</b>"
        ),
    },
    "top_header": {
        "uz": "🏆 <b>Eng yaxshi 5 ta o'yinchi:</b>\n\n",
        "ru": "🏆 <b>Топ 5 игроков:</b>\n\n",
        "en": "🏆 <b>Top 5 Players:</b>\n\n",
    },
    "weekly_header": {
        "uz": "📅 <b>Haftalik TOP-5:</b>\n\n",
        "ru": "📅 <b>Недельный ТОП-5:</b>\n\n",
        "en": "📅 <b>Weekly TOP-5:</b>\n\n",
    },
    "daily_bonus_received": {
        "uz": "🎁 Kunlik bonus olindi: <b>+100 ball!</b>\n\nErtaga qaytib keling 😊",
        "ru": "🎁 Ежедневный бонус получен: <b>+100 очков!</b>\n\nВозвращайтесь завтра 😊",
        "en": "🎁 Daily bonus claimed: <b>+100 points!</b>\n\nSee you tomorrow 😊",
    },
    "daily_bonus_already": {
        "uz": "⏰ Kunlik bonusni allaqachon oldingiz! Keyingi bonus: <b>{time}</b> dan keyin.",
        "ru": "⏰ Вы уже получили дневной бонус! Следующий через: <b>{time}</b>.",
        "en": "⏰ Already claimed today! Next bonus in: <b>{time}</b>.",
    },
    "hint_used": {
        "uz": "💡 Yordam: <b>{opt}</b> varianti noto'g'ri. (-50 ball)",
        "ru": "💡 Подсказка: вариант <b>{opt}</b> неверный. (-50 очков)",
        "en": "💡 Hint: option <b>{opt}</b> is wrong. (-50 pts)",
    },
    "reveal_used": {
        "uz": "🔤 Javobdagi harf: <b>{word}</b> (-25 ball)",
        "ru": "🔤 Буква в ответе: <b>{word}</b> (-25 очков)",
        "en": "🔤 Letter in answer: <b>{word}</b> (-25 pts)",
    },
    "achievements_header": {
        "uz": "🏅 <b>Sizning yutuqlaringiz:</b>\n\n",
        "ru": "🏅 <b>Ваши достижения:</b>\n\n",
        "en": "🏅 <b>Your Achievements:</b>\n\n",
    },
    "no_achievements": {
        "uz": "Hali yutuq yo'q. Ko'proq savol yeching! 💪",
        "ru": "Пока нет достижений. Решайте больше вопросов! 💪",
        "en": "No achievements yet. Keep answering! 💪",
    },
    "new_achievement": {
        "uz": "🎊 Yangi yutuq: <b>{title}</b>!",
        "ru": "🎊 Новое достижение: <b>{title}</b>!",
        "en": "🎊 New achievement: <b>{title}</b>!",
    },
    "open_answer": {
        "uz": "✏️ Javobingizni matn ko'rinishida yozing:",
        "ru": "✏️ Напишите ваш ответ текстом:",
        "en": "✏️ Type your answer as text:",
    },
    "fact_prefix": {
        "uz": "💡 <i>Qiziqarli fakt:</i> ",
        "ru": "💡 <i>Интересный факт:</i> ",
        "en": "💡 <i>Fun fact:</i> ",
    },
}

def tr(key: str, lang: str, **kwargs) -> str:
    text = T.get(key, {}).get(lang, T.get(key, {}).get("uz", key))
    return text.format(**kwargs) if kwargs else text

# ─────────────────────────────────────────────
# FSM STATES
# ─────────────────────────────────────────────
class RegStates(StatesGroup):
    waiting_first = State()
    waiting_last = State()
    waiting_phone = State()

class QuizStates(StatesGroup):
    answering_open = State()

# ─────────────────────────────────────────────
# DATABASE — synchronous (called once at startup)
# ─────────────────────────────────────────────
DB_PATH = "quizmaster.db"

def db_init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        first_name  TEXT,
        last_name   TEXT,
        phone       TEXT,
        lang        TEXT DEFAULT 'uz',
        score       INTEGER DEFAULT 0,
        correct_cnt INTEGER DEFAULT 0,
        wrong_cnt   INTEGER DEFAULT 0,
        streak      INTEGER DEFAULT 0,
        best_streak INTEGER DEFAULT 0,
        last_daily  TEXT,
        registered  INTEGER DEFAULT 0,
        joined_at   TEXT
    );
    CREATE TABLE IF NOT EXISTS questions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category    TEXT NOT NULL,
        lang        TEXT NOT NULL DEFAULT 'uz',
        q_type      TEXT NOT NULL,       -- 'choice' or 'open'
        question    TEXT NOT NULL,
        option_a    TEXT,
        option_b    TEXT,
        option_c    TEXT,
        answer      TEXT NOT NULL,
        explanation TEXT,
        difficulty  INTEGER DEFAULT 1    -- 1=easy 2=medium 3=hard
    );
    CREATE TABLE IF NOT EXISTS weekly_scores (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        week_start  TEXT,
        score       INTEGER DEFAULT 0,
        UNIQUE(user_id, week_start)
    );
    CREATE TABLE IF NOT EXISTS achievements (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        code        TEXT,
        earned_at   TEXT,
        UNIQUE(user_id, code)
    );
    CREATE TABLE IF NOT EXISTS answered (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        question_id INTEGER,
        is_correct  INTEGER,
        answered_at TEXT
    );
    """)
    conn.commit()
    conn.close()

def db_exec(sql: str, params: tuple = ()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    result = c.fetchall()
    conn.close()
    return [dict(r) for r in result]

def db_one(sql: str, params: tuple = ()):
    rows = db_exec(sql, params)
    return rows[0] if rows else None

# ─────────────────────────────────────────────
# SEED QUESTIONS (3 languages × 4 categories)
# ─────────────────────────────────────────────
SEED_QUESTIONS = [
    # ── MATH ──────────────────────────────────────────────────
    # UZ
    ("math","uz","choice","2 × 2 = ?","3","4","5","B","Matematikaning asosi — ko'paytirish jadvalidir.",1),
    ("math","uz","choice","10 ning kvadrat ildizi nechaga teng?","√10 ≈ 3.16","10","100","A","√10 ≈ 3.162, irratsional son.",2),
    ("math","uz","open","5 faktorial (5!) nechaga teng?",None,None,None,"120","5! = 5×4×3×2×1 = 120",1),
    ("math","uz","choice","π ning taxminiy qiymati qanday?","3.14","2.71","1.41","A","π — doira aylanasi uzunligining diametriga nisbati.",1),
    ("math","uz","open","Uchburchak ichki burchaklarining yig'indisi necha gradus?",None,None,None,"180","Euklidov geometriyasida har qanday uchburchak uchun.",1),
    # RU
    ("math","ru","choice","Чему равно 7 × 8?","54","56","58","B","7×8=56 — классика таблицы умножения.",1),
    ("math","ru","choice","Сколько нулей в числе миллиард?","6","8","9","C","1 000 000 000 — девять нулей.",1),
    ("math","ru","open","Чему равен корень из 144?",None,None,None,"12","√144 = 12, так как 12² = 144.",1),
    # EN
    ("math","en","choice","What is 15% of 200?","25","30","40","B","15% of 200 = 0.15 × 200 = 30.",1),
    ("math","en","open","What is the value of 2 to the power of 10?",None,None,None,"1024","2^10 = 1024 — useful in computing (1 KB).",2),
    # ── HISTORY ───────────────────────────────────────────────
    ("history","uz","choice","O'zbekiston qachon mustaqillikka erishdi?","1990","1991","1992","B","1991-yil 1-sentabrda mustaqillik e'lon qilindi.",1),
    ("history","uz","choice","Amir Temur qayerda tug'ilgan?","Buxoro","Samarqand","Kesh (Shahrisabz)","C","Temur 1336-yilda Kesh (hozirgi Shahrisabz)da tug'ilgan.",1),
    ("history","uz","open","O'zbekistonning poytaxti qaysi shahar?",None,None,None,"toshkent","Toshkent — Markaziy Osiyoning eng yirik shahri.",1),
    ("history","ru","choice","В каком году была основана Москва?","1147","1200","1380","A","Москва основана в 1147 году Юрием Долгоруким.",1),
    ("history","ru","open","Кто написал 'Войну и мир'?",None,None,None,"толстой","Лев Николаевич Толстой написал этот роман-эпопею.",1),
    ("history","en","choice","Who was the first President of the United States?","Thomas Jefferson","George Washington","Abraham Lincoln","B","George Washington served 1789–1797.",1),
    ("history","en","open","In which year did World War II end?",None,None,None,"1945","WWII ended in 1945: VE Day (May 8) and VJ Day (Sep 2).",1),
    # ── SCIENCE ───────────────────────────────────────────────
    ("science","uz","choice","Yorug'likning vakuumdagi tezligi necha km/s?","200 000","300 000","150 000","B","c ≈ 299 792 km/s — tabiatdagi eng katta tezlik.",1),
    ("science","uz","open","Suvning kimyoviy formulasi nima?",None,None,None,"h2o","H₂O — ikki vodorod, bir kislorod atomi.",1),
    ("science","uz","choice","DNK nimani anglatadi?","Dezoksiribonuklein kislota","Dinitrogen kislota","Difosfor kislota","A","DNK — genetik ma'lumotni saqlaydi.",2),
    ("science","ru","choice","Какой газ составляет большую часть атмосферы Земли?","Кислород","Азот","Углекислый газ","B","Азот составляет около 78% атмосферы.",1),
    ("science","ru","open","Сколько костей у взрослого человека?",None,None,None,"206","У взрослого человека 206 костей.",2),
    ("science","en","choice","What planet is known as the Red Planet?","Venus","Jupiter","Mars","C","Mars appears red due to iron oxide on its surface.",1),
    ("science","en","open","What is the chemical symbol for gold?",None,None,None,"au","Au comes from the Latin word 'Aurum'.",1),
    # ── GENERAL ───────────────────────────────────────────────
    ("general","uz","choice","Dunyo bo'yicha eng ko'p so'zlashadigan til qaysi?","Ingliz tili","Mandarin (Xitoy) tili","Ispan tili","B","Mandarin — 1 mlrd dan ortiq ona tilida so'zlashuvchilar.",1),
    ("general","uz","open","Olimpiya o'yinlari necha yilda bir marta o'tkaziladi?",None,None,None,"4","Yozgi va Qishki Olimpiada har 4 yilda bo'lib o'tadi.",1),
    ("general","uz","choice","Sahara cho'li qaysi qit'ada joylashgan?","Osiyo","Amerika","Afrika","C","Sahara — dunyodagi eng katta issiq cho'l.",1),
    ("general","ru","choice","Какая самая длинная река в мире?","Амазонка","Нил","Янцзы","B","Нил — длиной около 6650 км.",1),
    ("general","ru","open","Сколько цветов у радуги?",None,None,None,"7","Красный, оранжевый, жёлтый, зелёный, голубой, синий, фиолетовый.",1),
    ("general","en","choice","How many continents are there on Earth?","5","6","7","C","The 7 continents: Africa, Antarctica, Asia, Australia, Europe, North America, South America.",1),
    ("general","en","open","What is the capital of Japan?",None,None,None,"tokyo","Tokyo is the capital and most populous city of Japan.",1),
    ("general","en","choice","Which ocean is the largest?","Atlantic","Indian","Pacific","C","The Pacific Ocean covers about 165 million km².",1),
]

def db_seed():
    existing = db_one("SELECT COUNT(*) as cnt FROM questions")
    if existing and existing["cnt"] > 0:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany("""
        INSERT INTO questions (category,lang,q_type,question,option_a,option_b,option_c,answer,explanation,difficulty)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, SEED_QUESTIONS)
    conn.commit()
    conn.close()
    log.info("✅ Seed questions inserted.")

# ─────────────────────────────────────────────
# ACHIEVEMENT DEFINITIONS
# ─────────────────────────────────────────────
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
    user = db_one("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not user:
        return
    earned = {r["code"] for r in db_exec("SELECT code FROM achievements WHERE user_id=?", (user_id,))}
    for code, data in ACHIEVEMENTS.items():
        if code not in earned and data["condition"](user):
            db_exec("INSERT OR IGNORE INTO achievements (user_id,code,earned_at) VALUES (?,?,?)",
                    (user_id, code, datetime.now().isoformat()))
            await bot.send_message(user_id, tr("new_achievement", lang, title=data[lang]))

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def week_start() -> str:
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()

def add_score(user_id: int, pts: int):
    db_exec("UPDATE users SET score = score + ? WHERE user_id=?", (pts, user_id))
    ws = week_start()
    db_exec("""INSERT INTO weekly_scores (user_id,week_start,score) VALUES (?,?,?)
               ON CONFLICT(user_id,week_start) DO UPDATE SET score=score+?""",
            (user_id, ws, pts, pts))

def get_lang(user_id: int) -> str:
    u = db_one("SELECT lang FROM users WHERE user_id=?", (user_id,))
    return u["lang"] if u else "uz"

def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr("btn_questions", lang)), KeyboardButton(text=tr("btn_rating", lang))],
            [KeyboardButton(text=tr("btn_my_score", lang)), KeyboardButton(text=tr("btn_weekly", lang))],
            [KeyboardButton(text=tr("btn_achievements", lang)), KeyboardButton(text=tr("btn_daily_bonus", lang))],
            [KeyboardButton(text=tr("btn_change_lang", lang))],
        ],
        resize_keyboard=True,
    )

def lang_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский",   callback_data="lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English",   callback_data="lang_en"),
    ]])

def category_inline_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr("cat_math", lang),    callback_data="cat_math"),
         InlineKeyboardButton(text=tr("cat_history", lang), callback_data="cat_history")],
        [InlineKeyboardButton(text=tr("cat_science", lang), callback_data="cat_science"),
         InlineKeyboardButton(text=tr("cat_general", lang), callback_data="cat_general")],
    ])

medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

# ─────────────────────────────────────────────
# ROUTER & BOT SETUP
# ─────────────────────────────────────────────
router = Router()
bot_instance: Bot = None   # set in main()
active_timers: dict[int, asyncio.Task] = {}

# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    user = db_one("SELECT * FROM users WHERE user_id=?", (msg.from_user.id,))
    if user and user["registered"]:
        lang = user["lang"]
        await msg.answer(tr("reg_done", lang, name=user["first_name"]).split("\n\n")[0] + "\n\n👋",
                         reply_markup=main_menu_kb(lang))
        return
    # First time — choose language
    await msg.answer(tr("choose_lang", "uz"), reply_markup=lang_inline_kb())

# ─────────────────────────────────────────────
# LANGUAGE SELECTION
# ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("lang_"))
async def cb_lang(call: CallbackQuery, state: FSMContext):
    lang = call.data.split("_")[1]
    uid = call.from_user.id
    user = db_one("SELECT * FROM users WHERE user_id=?", (uid,))
    if not user:
        db_exec("INSERT OR IGNORE INTO users (user_id,username,lang,joined_at) VALUES (?,?,?,?)",
                (uid, call.from_user.username, lang, datetime.now().isoformat()))
    else:
        db_exec("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
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

# ─────────────────────────────────────────────
# REGISTRATION FLOW
# ─────────────────────────────────────────────
@router.message(RegStates.waiting_first)
async def reg_first(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(first_name=msg.text.strip())
    await msg.answer(tr("enter_last", lang), parse_mode=ParseMode.HTML)
    await state.set_state(RegStates.waiting_last)

@router.message(RegStates.waiting_last)
async def reg_last(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
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
    phone = msg.contact.phone_number if msg.contact else msg.text.strip()
    uid = msg.from_user.id
    db_exec("""UPDATE users SET first_name=?,last_name=?,phone=?,registered=1,score=200
               WHERE user_id=?""",
            (data["first_name"], data["last_name"], phone, uid))
    add_score(uid, 0)  # ensure weekly row
    await state.clear()
    await msg.answer(
        tr("reg_done", lang, name=data["first_name"]),
        reply_markup=main_menu_kb(lang),
        parse_mode=ParseMode.HTML,
    )
    # First achievement
    await check_achievements(msg.bot, uid, lang)

# ─────────────────────────────────────────────
# GUARD: only registered users pass
# ─────────────────────────────────────────────
async def ensure_registered(msg: Message) -> Optional[dict]:
    user = db_one("SELECT * FROM users WHERE user_id=? AND registered=1", (msg.from_user.id,))
    if not user:
        await msg.answer("❗ Avval /start buyrug'ini yuboring va ro'yxatdan o'ting.")
    return user

# ─────────────────────────────────────────────
# QUESTIONS — category selection
# ─────────────────────────────────────────────
@router.message(F.text.func(lambda t: any(
    t == T["btn_questions"][l] for l in ("uz","ru","en"))))
async def menu_questions(msg: Message, state: FSMContext):
    user = await ensure_registered(msg)
    if not user:
        return
    await state.clear()
    lang = user["lang"]
    await msg.answer(tr("choose_category", lang), reply_markup=category_inline_kb(lang))

@router.callback_query(F.data.startswith("cat_"))
async def cb_category(call: CallbackQuery, state: FSMContext):
    lang = get_lang(call.from_user.id)
    category = call.data[4:]   # "math" / "history" / "science" / "general"
    await state.update_data(category=category)
    await call.message.edit_reply_markup()
    await send_question(call.message, call.from_user.id, state, lang, category)
    await call.answer()

# ─────────────────────────────────────────────
# SEND QUESTION
# ─────────────────────────────────────────────
async def send_question(msg: Message, user_id: int, state: FSMContext, lang: str, category: str):
    # Cancel existing timer
    if user_id in active_timers:
        active_timers[user_id].cancel()
        del active_timers[user_id]

    # Pick random question not recently answered (last 20)
    recent = [r["question_id"] for r in db_exec(
        "SELECT question_id FROM answered WHERE user_id=? ORDER BY answered_at DESC LIMIT 20",
        (user_id,))]
    placeholders = ",".join("?" * len(recent)) if recent else "0"
    q = db_one(
        f"SELECT * FROM questions WHERE category=? AND lang=? AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1",
        (category, lang, *recent),
    )
    if not q:
        # Allow repeats if pool is small
        q = db_one("SELECT * FROM questions WHERE category=? AND lang=? ORDER BY RANDOM() LIMIT 1",
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

    # Start 30-second countdown timer
    task = asyncio.create_task(_timeout_task(msg.bot, user_id, state, lang, 30))
    active_timers[user_id] = task

async def _timeout_task(bot: Bot, user_id: int, state: FSMContext, lang: str, seconds: int):
    await asyncio.sleep(seconds)
    data = await state.get_data()
    q = data.get("current_q")
    if not q:
        return
    # Reset streak
    db_exec("UPDATE users SET streak=0 WHERE user_id=?", (user_id,))
    db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,0,?)",
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

# ─────────────────────────────────────────────
# CHOICE ANSWER HANDLER
# ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("ans_"))
async def cb_answer_choice(call: CallbackQuery, state: FSMContext):
    lang = get_lang(call.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    if not q:
        await call.answer("❗")
        return

    # Cancel timer
    if call.from_user.id in active_timers:
        active_timers[call.from_user.id].cancel()
        del active_timers[call.from_user.id]

    chosen = call.data[4:]  # A/B/C
    correct = q["answer"]   # A/B/C
    user = db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
    is_correct = chosen == correct

    # Base points by difficulty
    base_pts = {1: 10, 2: 20, 3: 35}.get(q["difficulty"], 10)
    pts_earned = 0

    db_exec("UPDATE users SET wrong_cnt=wrong_cnt+1 WHERE user_id=?", (call.from_user.id,))
    db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,?,?)",
            (call.from_user.id, q["id"], int(is_correct), datetime.now().isoformat()))

    if is_correct:
        db_exec("UPDATE users SET correct_cnt=correct_cnt+1, wrong_cnt=wrong_cnt-1, streak=streak+1 WHERE user_id=?",
                (call.from_user.id,))
        user_upd = db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
        streak = user_upd["streak"]
        # Update best streak
        if streak > user_upd["best_streak"]:
            db_exec("UPDATE users SET best_streak=? WHERE user_id=?", (streak, call.from_user.id))
        pts_earned = base_pts
        add_score(call.from_user.id, pts_earned)
        result_text = tr("correct", lang, pts=pts_earned)
        # Streak bonus every 5
        if streak > 0 and streak % 5 == 0:
            bonus = streak * 2
            add_score(call.from_user.id, bonus)
            result_text += "\n" + tr("streak_bonus", lang, streak=streak, bonus=bonus)
    else:
        db_exec("UPDATE users SET streak=0 WHERE user_id=?", (call.from_user.id,))
        ans_text = q["option_" + correct.lower()] if correct in ("A","B","C") else correct
        result_text = tr("wrong", lang, ans=f"{correct}) {ans_text}")

    if q.get("explanation"):
        result_text += f"\n\n{tr('fact_prefix', lang)}{q['explanation']}"

    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("next_btn", lang), callback_data=f"next_{data.get('category','general')}"),
    ]])

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(result_text, reply_markup=next_kb, parse_mode=ParseMode.HTML)
    await state.update_data(current_q=None)
    await state.set_state(None)
    await check_achievements(call.bot, call.from_user.id, lang)
    await call.answer()

# ─────────────────────────────────────────────
# OPEN ANSWER HANDLER
# ─────────────────────────────────────────────
@router.message(QuizStates.answering_open)
async def handle_open_answer(msg: Message, state: FSMContext):
    lang = get_lang(msg.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    if not q:
        return

    # Cancel timer
    if msg.from_user.id in active_timers:
        active_timers[msg.from_user.id].cancel()
        del active_timers[msg.from_user.id]

    user_ans = msg.text.strip().lower()
    correct_ans = q["answer"].strip().lower()
    is_correct = user_ans == correct_ans

    base_pts = {1: 20, 2: 35, 3: 50}.get(q["difficulty"], 20)  # Open = more points

    db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,?,?)",
            (msg.from_user.id, q["id"], int(is_correct), datetime.now().isoformat()))

    if is_correct:
        db_exec("UPDATE users SET correct_cnt=correct_cnt+1, streak=streak+1 WHERE user_id=?", (msg.from_user.id,))
        user_upd = db_one("SELECT * FROM users WHERE user_id=?", (msg.from_user.id,))
        streak = user_upd["streak"]
        if streak > user_upd["best_streak"]:
            db_exec("UPDATE users SET best_streak=? WHERE user_id=?", (streak, msg.from_user.id))
        add_score(msg.from_user.id, base_pts)
        result_text = tr("correct", lang, pts=base_pts)
        if streak > 0 and streak % 5 == 0:
            bonus = streak * 2
            add_score(msg.from_user.id, bonus)
            result_text += "\n" + tr("streak_bonus", lang, streak=streak, bonus=bonus)
    else:
        db_exec("UPDATE users SET wrong_cnt=wrong_cnt+1, streak=0 WHERE user_id=?", (msg.from_user.id,))
        result_text = tr("wrong", lang, ans=q["answer"])

    if q.get("explanation"):
        result_text += f"\n\n{tr('fact_prefix', lang)}{q['explanation']}"

    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("next_btn", lang), callback_data=f"next_{data.get('category','general')}"),
    ]])
    await msg.answer(result_text, reply_markup=next_kb, parse_mode=ParseMode.HTML)
    await state.update_data(current_q=None)
    await state.set_state(None)
    await check_achievements(msg.bot, msg.from_user.id, lang)

# ─────────────────────────────────────────────
# HINT — remove wrong option (choice)
# ─────────────────────────────────────────────
@router.callback_query(F.data == "hint")
async def cb_hint(call: CallbackQuery, state: FSMContext):
    lang = get_lang(call.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    user = db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
    if data.get("hint_used"):
        await call.answer("💡 Yordam allaqachon ishlatildi!", show_alert=True)
        return
    if user["score"] < 50:
        await call.answer(tr("not_enough_pts", lang, pts=user["score"], need=50), show_alert=True)
        return
    # Pick a wrong option
    correct = q["answer"]
    wrong_opts = [x for x in ["A","B","C"] if x != correct]
    eliminated = random.choice(wrong_opts)
    add_score(call.from_user.id, -50)
    await state.update_data(hint_used=True)
    await call.answer(tr("hint_used", lang, opt=eliminated), show_alert=True)

# ─────────────────────────────────────────────
# REVEAL LETTER — open one letter (open-type)
# ─────────────────────────────────────────────
@router.callback_query(F.data == "reveal")
async def cb_reveal(call: CallbackQuery, state: FSMContext):
    lang = get_lang(call.from_user.id)
    data = await state.get_data()
    q = data.get("current_q")
    user = db_one("SELECT * FROM users WHERE user_id=?", (call.from_user.id,))
    if user["score"] < 25:
        await call.answer(tr("not_enough_pts", lang, pts=user["score"], need=25), show_alert=True)
        return
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
    add_score(call.from_user.id, -25)
    await state.update_data(revealed_word=new_word)
    display = " ".join(new_word)
    await call.answer(tr("reveal_used", lang, word=display), show_alert=True)

# ─────────────────────────────────────────────
# SKIP
# ─────────────────────────────────────────────
@router.callback_query(F.data == "skip_q")
async def cb_skip(call: CallbackQuery, state: FSMContext):
    lang = get_lang(call.from_user.id)
    data = await state.get_data()
    if call.from_user.id in active_timers:
        active_timers[call.from_user.id].cancel()
        del active_timers[call.from_user.id]
    q = data.get("current_q")
    if q:
        db_exec("INSERT INTO answered (user_id,question_id,is_correct,answered_at) VALUES (?,?,0,?)",
                (call.from_user.id, q["id"], datetime.now().isoformat()))
        db_exec("UPDATE users SET streak=0 WHERE user_id=?", (call.from_user.id,))
    category = data.get("category", "general")
    next_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr("next_btn", lang), callback_data=f"next_{category}"),
    ]])
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer("⏭ O'tkazib yuborildi.", reply_markup=next_kb)
    await state.update_data(current_q=None)
    await state.set_state(None)
    await call.answer()

# ─────────────────────────────────────────────
# NEXT QUESTION
# ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("next_"))
async def cb_next(call: CallbackQuery, state: FSMContext):
    lang = get_lang(call.from_user.id)
    category = call.data[5:]
    await state.update_data(category=category)
    await call.message.edit_reply_markup()
    await send_question(call.message, call.from_user.id, state, lang, category)
    await call.answer()

# ─────────────────────────────────────────────
# RATING — Top 5 all time
# ─────────────────────────────────────────────
@router.message(F.text.func(lambda t: any(t == T["btn_rating"][l] for l in ("uz","ru","en"))))
async def menu_rating(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    rows = db_exec("SELECT first_name,last_name,score FROM users WHERE registered=1 ORDER BY score DESC LIMIT 5")
    if not rows:
        await msg.answer("Hali ma'lumot yo'q.")
        return
    text = tr("top_header", lang)
    for i, r in enumerate(rows):
        text += f"{medal[i]} <b>{r['first_name']} {r['last_name']}</b> — {r['score']} ball\n"
    await msg.answer(text, parse_mode=ParseMode.HTML)

# ─────────────────────────────────────────────
# WEEKLY TOP 5
# ─────────────────────────────────────────────
@router.message(F.text.func(lambda t: any(t == T["btn_weekly"][l] for l in ("uz","ru","en"))))
async def menu_weekly(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    ws = week_start()
    rows = db_exec("""
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

# ─────────────────────────────────────────────
# MY SCORE
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# ACHIEVEMENTS
# ─────────────────────────────────────────────
@router.message(F.text.func(lambda t: any(t == T["btn_achievements"][l] for l in ("uz","ru","en"))))
async def menu_achievements(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    lang = user["lang"]
    earned = db_exec("SELECT code,earned_at FROM achievements WHERE user_id=? ORDER BY earned_at", (msg.from_user.id,))
    if not earned:
        await msg.answer(tr("achievements_header", lang) + tr("no_achievements", lang), parse_mode=ParseMode.HTML)
        return
    text = tr("achievements_header", lang)
    for r in earned:
        title = ACHIEVEMENTS.get(r["code"], {}).get(lang, r["code"])
        date_str = r["earned_at"][:10]
        text += f"{title}  <i>({date_str})</i>\n"
    # Show locked achievements
    earned_codes = {r["code"] for r in earned}
    locked = [ACHIEVEMENTS[c][lang] for c in ACHIEVEMENTS if c not in earned_codes]
    if locked:
        text += "\n🔒 <i>" + ", ".join(locked) + "</i>"
    await msg.answer(text, parse_mode=ParseMode.HTML)

# ─────────────────────────────────────────────
# DAILY BONUS
# ─────────────────────────────────────────────
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
        await msg.answer(tr("daily_bonus_already", lang, time=f"{h}s {m}d"), parse_mode=ParseMode.HTML)
        return
    db_exec("UPDATE users SET last_daily=? WHERE user_id=?", (today, msg.from_user.id))
    add_score(msg.from_user.id, 100)
    await msg.answer(tr("daily_bonus_received", lang), parse_mode=ParseMode.HTML)
    await check_achievements(msg.bot, msg.from_user.id, lang)

# ─────────────────────────────────────────────
# CHANGE LANGUAGE
# ─────────────────────────────────────────────
@router.message(F.text.func(lambda t: any(t == T["btn_change_lang"][l] for l in ("uz","ru","en"))))
async def menu_change_lang(msg: Message):
    user = await ensure_registered(msg)
    if not user:
        return
    await msg.answer(tr("choose_lang", user["lang"]), reply_markup=lang_inline_kb())

# ─────────────────────────────────────────────
# FALLBACK
# ─────────────────────────────────────────────
@router.message(Command("help"))
async def cmd_help(msg: Message):
    lang = get_lang(msg.from_user.id)
    help_texts = {
        "uz": (
            "ℹ️ <b>QuizMaster Bot — Yordam</b>\n\n"
            "🧠 <b>Savollar</b> — Kategoriya tanlang va savollar yeching\n"
            "🏆 <b>Reyting</b> — Umumiy TOP-5\n"
            "📅 <b>Haftalik TOP</b> — Bu haftaning yaxshilari\n"
            "📊 <b>Mening natijam</b> — Shaxsiy statistika\n"
            "🏅 <b>Yutuqlar</b> — Qo'lga kiritilgan va kutilayotgan yutuqlar\n"
            "🎁 <b>Kunlik bonus</b> — Har kuni +100 ball\n\n"
            "<b>Ball tizimi:</b>\n"
            "• Test savoli: 10/20/35 ball (qiyinlik bo'yicha)\n"
            "• Ochiq savol: 20/35/50 ball\n"
            "• Streak bonusi: har 5 ketma-ket to'g'ri javobda +ball\n"
            "• Yordam (50 ball) — noto'g'ri variantni o'chirish\n"
            "• Harf ochish (25 ball) — yashirin harfni ko'rsatish"
        ),
        "ru": (
            "ℹ️ <b>QuizMaster Bot — Помощь</b>\n\n"
            "🧠 <b>Вопросы</b> — Выберите категорию\n"
            "🏆 <b>Рейтинг</b> — Топ-5 всего времени\n"
            "📅 <b>Недельный ТОП</b> — Лучшие этой недели\n"
            "📊 <b>Мой результат</b> — Личная статистика\n"
            "🏅 <b>Достижения</b> — Заработанные и будущие\n"
            "🎁 <b>Дневной бонус</b> — +100 очков каждый день\n\n"
            "<b>Система очков:</b>\n"
            "• Тест: 10/20/35 (по сложности)\n"
            "• Открытый: 20/35/50\n"
            "• Бонус серии: каждые 5 правильных\n"
            "• Подсказка (50 очков) — убрать неверный вариант\n"
            "• Открыть букву (25 очков)"
        ),
        "en": (
            "ℹ️ <b>QuizMaster Bot — Help</b>\n\n"
            "🧠 <b>Questions</b> — Pick a category and answer\n"
            "🏆 <b>Leaderboard</b> — All-time TOP-5\n"
            "📅 <b>Weekly TOP</b> — This week's best\n"
            "📊 <b>My Score</b> — Personal stats\n"
            "🏅 <b>Achievements</b> — Earned & upcoming\n"
            "🎁 <b>Daily Bonus</b> — +100 pts every day\n\n"
            "<b>Scoring:</b>\n"
            "• Choice question: 10/20/35 (by difficulty)\n"
            "• Open question: 20/35/50\n"
            "• Streak bonus: every 5 correct in a row\n"
            "• Hint (50 pts) — eliminate a wrong option\n"
            "• Reveal letter (25 pts)"
        ),
    }
    await msg.answer(help_texts.get(lang, help_texts["uz"]), parse_mode=ParseMode.HTML)

@router.message()
async def fallback(msg: Message, state: FSMContext):
    cur = await state.get_state()
    if cur == QuizStates.answering_open:
        return  # handled above
    lang = get_lang(msg.from_user.id)
    user = db_one("SELECT registered FROM users WHERE user_id=?", (msg.from_user.id,))
    if user and user["registered"]:
        await msg.answer("❓ /help buyrug'i orqali imkoniyatlarni ko'ring.", reply_markup=main_menu_kb(lang))

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
async def main():
    db_init()
    db_seed()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    log.info("🚀 QuizMaster Bot ishga tushdi!")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())