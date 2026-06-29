from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.translations import tr

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
