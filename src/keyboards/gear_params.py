from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_season_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton("Зима"), KeyboardButton("Весна"))
    kb.row(KeyboardButton("Лето"), KeyboardButton("Осень"))
    return kb


def get_experience_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton("Новичок"), KeyboardButton("Опытный"))
    return kb
