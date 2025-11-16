from aiogram import types
from aiogram.dispatcher import Dispatcher

from keyboards.main_menu import get_region_keyboard
from keyboards.route_menu import build_routes_list_keyboard
from services.routes_service import get_routes_by_region


# Карта текстов кнопок -> внутренний код региона
REGION_BUTTONS = {
    "🇷🇺 Россия": "russia",
    "🏞 Смоленская область (CRT67)": "smolensk_crt67",
    "🇱🇻 Латвия": "latvia",
    "🌍 Мир": "world",
}


def register_location_handlers(dp: Dispatcher) -> None:
    """
    Хендлеры выбора региона.
    """

    @dp.message_handler(lambda message: message.text in REGION_BUTTONS.keys())
    async def handle_region_choice(message: types.Message) -> None:
        human_name = message.text
        region_code = REGION_BUTTONS[message.text]

        try:
            routes = get_routes_by_region(region_code)
        except Exception as e:
            await message.answer(
                f"Не удалось загрузить маршруты для региона {human_name}.\n"
                f"Техническая ошибка: {e}"
            )
            return

        if not routes:
            await message.answer(
                f"Для региона {human_name} пока нет маршрутов. "
                "Позже мы добавим сюда треки."
            )
            return

        await message.answer(
            f"Маршруты в регионе: <b>{human_name}</b>\n\n"
            "Выбери один из маршрутов ниже:",
            reply_markup=build_routes_list_keyboard(region_code, routes),
        )

    # На будущее: хендлер для возврата в главное меню
    @dp.message_handler(commands=["menu"])
    async def cmd_menu(message: types.Message) -> None:
        await message.answer("Выбери регион:", reply_markup=get_region_keyboard())
