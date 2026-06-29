from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.translations import tr

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
