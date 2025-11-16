from aiogram import types
from aiogram.dispatcher import Dispatcher

from keyboards.main_menu import get_region_keyboard


def register_start_handlers(dp: Dispatcher) -> None:
    """Регистрация хендлеров стартового сценария (/start и приветствие)."""

    @dp.message_handler(commands=["start"])
    async def cmd_start(message: types.Message) -> None:
        text = (
            "Привет! Я Gear Checklist Bot 👋\n\n"
            "Я помогу подобрать снаряжение под маршрут и условия похода.\n"
            "Для начала выбери регион:"
        )
        await message.answer(text, reply_markup=get_region_keyboard())
