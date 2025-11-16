from io import BytesIO

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputFile

from keyboards.gear_params import get_season_keyboard, get_experience_keyboard
from services.routes_service import get_route_by_index
from services.gear_service import generate_gear_list, get_region_notes
from services.pdf_service import generate_gear_pdf


SEASON_MAP = {
    "Зима": "winter",
    "Весна": "spring",
    "Лето": "summer",
    "Осень": "autumn",
}

EXPERIENCE_MAP = {
    "Новичок": "beginner",
    "Опытный": "advanced",
}


class GearStates(StatesGroup):
    waiting_participants = State()
    waiting_days = State()
    waiting_season = State()
    waiting_experience = State()


def register_gear_flow_handlers(dp: Dispatcher) -> None:
    @dp.callback_query_handler(lambda c: c.data.startswith("route_gear|"))
    async def on_route_gear(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """
        Старт сценария подбора снаряжения.
        Формат callback_data: route_gear|region_code|route_index
        """
        _, region_code, idx_str = callback_query.data.split("|", maxsplit=2)

        try:
            route_index = int(idx_str)
        except ValueError:
            await callback_query.message.answer("Не удалось распознать маршрут для подбора снаряжения.")
            await callback_query.answer()
            return

        route = get_route_by_index(region_code, route_index)
        if not route:
            await callback_query.message.answer("Маршрут не найден. Попробуй начать заново.")
            await callback_query.answer()
            return

        await state.update_data(
            region_code=region_code,
            route_index=route_index,
            route_title=route["title"],
        )

        await callback_query.message.answer(
            "Начинаем подбор снаряжения для маршрута:\n"
            f"<b>{route['title']}</b>\n\n"
            "Сначала укажи количество участников похода (введи число, например 3)."
        )
        await GearStates.waiting_participants.set()
        await callback_query.answer()

    @dp.message_handler(state=GearStates.waiting_participants)
    async def process_participants(message: types.Message, state: FSMContext) -> None:
        try:
            participants = int(message.text)
            if participants <= 0:
                raise ValueError
        except ValueError:
            await message.answer("Нужно ввести положительное целое число участников, например 3.")
            return

        await state.update_data(participants=participants)
        await GearStates.waiting_days.set()
        await message.answer("Сколько дней длится поход? Введи число, например 2.")

    @dp.message_handler(state=GearStates.waiting_days)
    async def process_days(message: types.Message, state: FSMContext) -> None:
        try:
            days = int(message.text)
            if days <= 0:
                raise ValueError
        except ValueError:
            await message.answer("Нужно ввести положительное целое число дней, например 2.")
            return

        await state.update_data(days=days)
        await GearStates.waiting_season.set()
        await message.answer(
            "Выбери сезон похода:",
            reply_markup=get_season_keyboard(),
        )

    @dp.message_handler(state=GearStates.waiting_season)
    async def process_season(message: types.Message, state: FSMContext) -> None:
        text = message.text.strip()
        if text not in SEASON_MAP:
            await message.answer("Пожалуйста, выбери сезон, используя кнопки на клавиатуре.")
            return

        season_code = SEASON_MAP[text]
        await state.update_data(season=season_code, season_human=text)
        await GearStates.waiting_experience.set()
        await message.answer(
            "Уровень опыта группы?",
            reply_markup=get_experience_keyboard(),
        )

    @dp.message_handler(state=GearStates.waiting_experience)
    async def process_experience(message: types.Message, state: FSMContext) -> None:
        text = message.text.strip()
        if text not in EXPERIENCE_MAP:
            await message.answer("Пожалуйста, выбери уровень опыта с помощью кнопок.")
            return

        exp_code = EXPERIENCE_MAP[text]
        await state.update_data(experience=exp_code, experience_human=text)

        data = await state.get_data()
        region_code = data["region_code"]
        route_index = data["route_index"]
        route_title = data["route_title"]
        participants = data["participants"]
        days = data["days"]
        season_code = data["season"]
        exp_code = data["experience"]
        season_human = data["season_human"]
        exp_human = data["experience_human"]

        # Получаем маршрут целиком (для PDF и QR)
        route = get_route_by_index(region_code, route_index)

        # Генерация списков снаряжения
        gear = generate_gear_list(
            region_code=region_code,
            participants=participants,
            days=days,
            season=season_code,
            experience_level=exp_code,
        )
        region_notes = get_region_notes(region_code)

        # Текстовый черновой чек-лист
        lines = []
        lines.append("🎒 <b>Черновой чек-лист снаряжения</b>")
        lines.append(f"Маршрут: {route_title}")
        lines.append(f"Участников: {participants}, длительность: {days} дн.")
        lines.append(f"Сезон: {season_human}, опыт группы: {exp_human}")
        lines.append("")

        if region_notes:
            lines.append("Особенности региона:")
            lines.append(region_notes)
            lines.append("")

        group_items = gear.get("group", [])
        personal_items = gear.get("personal", [])

        if group_items:
            lines.append("<b>Групповое снаряжение:</b>")
            for item in group_items:
                lines.append(
                    f"- [{item['category']}] {item['name']} — {item['quantity']} шт."
                )
            lines.append("")
        else:
            lines.append("Групповое снаряжение: ничего обязательного не найдено.")
            lines.append("")

        if personal_items:
            lines.append("<b>Личное снаряжение (на каждого участника):</b>")
            for item in personal_items:
                lines.append(
                    f"- [{item['category']}] {item['name']} — {item['quantity_per_person']} шт. на человека"
                )
        else:
            lines.append("Личное снаряжение: ничего обязательного не найдено.")

        await message.answer("\n".join(lines), reply_markup=None)

        # Генерируем PDF
        try:
            pdf_bytes, filename = generate_gear_pdf(
                route=route,
                participants=participants,
                days=days,
                season_human=season_human,
                experience_human=exp_human,
                gear=gear,
                region_notes=region_notes,
            )

            pdf_io = BytesIO(pdf_bytes)
            pdf_io.name = filename

            await message.answer_document(
                InputFile(pdf_io, filename=filename),
                caption="Вот PDF-чек-лист с QR-кодом маршрута.",
            )
        except Exception as e:
            await message.answer(
                f"Не удалось сформировать PDF-файл чек-листа.\n"
                f"Техническая ошибка: {e}"
            )

        await state.finish()
