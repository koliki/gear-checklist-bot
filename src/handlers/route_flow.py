from aiogram import types
from aiogram.dispatcher import Dispatcher

from keyboards.route_menu import build_route_detail_keyboard
from services.routes_service import get_route_by_index


def register_route_flow_handlers(dp: Dispatcher) -> None:
    """
    Хендлеры, связанные с выбором конкретного маршрута
    (показ карточки маршрута и кнопок действий).
    """

    @dp.callback_query_handler(lambda c: c.data.startswith("route_sel|"))
    async def on_route_selected(callback_query: types.CallbackQuery) -> None:
        """
        Пользователь выбрал маршрут из списка.
        Формат callback_data: route_sel|region_code|index
        """
        _, region_code, idx_str = callback_query.data.split("|", maxsplit=2)

        try:
            index = int(idx_str)
        except ValueError:
            await callback_query.message.answer("Не удалось распознать выбранный маршрут.")
            await callback_query.answer()
            return

        route = get_route_by_index(region_code, index)
        if not route:
            await callback_query.message.answer("Маршрут не найден. Попробуй выбрать снова.")
            await callback_query.answer()
            return

        text = (
            f"🏕 <b>{route['title']}</b>\n\n"
            f"Регион: {route['region']}, страна: {route['country']}\n"
            f"Дистанция: {route['distance_km']} км\n"
            f"Рекомендуемая длительность: {route['duration_days']} дн.\n"
            f"Сложность: {route['difficulty']}\n"
            f"Сезон: {route['season']}\n\n"
            f"{route['description_short']}"
        )

        await callback_query.message.answer(
            text,
            reply_markup=build_route_detail_keyboard(region_code, index, route),
        )
        await callback_query.answer()
