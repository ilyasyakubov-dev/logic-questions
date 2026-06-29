# pyrefly: ignore [missing-import]
from aiogram import Router
# pyrefly: ignore [missing-import]
from aiogram.filters import Command
# pyrefly: ignore [missing-import]
from aiogram.types import Message
# pyrefly: ignore [missing-import]
from aiogram.enums import ParseMode

from utils.helpers import get_lang

router = Router()

@router.message(Command("help"))
async def cmd_help(msg: Message):
    # pyrefly: ignore [missing-attribute]
    lang = await get_lang(msg.from_user.id)
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
