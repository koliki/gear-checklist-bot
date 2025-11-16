from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_region_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню выбора региона."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    row1 = [
        KeyboardButton("🇷🇺 Россия"),
        KeyboardButton("🏞 Смоленская область (CRT67)"),
    ]
    row2 = [
        KeyboardButton("🇱🇻 Латвия"),
        KeyboardButton("🌍 Мир"),
    ]

    kb.row(*row1)
    kb.row(*row2)

    return kb
