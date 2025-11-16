from typing import List, Dict

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _is_valid_url(url: str) -> bool:
    """
    Простейшая проверка URL: должен начинаться с http:// или https://.
    Если строка пустая или не похожа на URL, считаем её невалидной.
    """
    if not isinstance(url, str):
        return False
    url = url.strip()
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")


def build_routes_list_keyboard(region_code: str, routes: List[Dict]) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком маршрутов в регионе.
    В callback_data передаём индекс маршрута (0, 1, 2...),
    чтобы не упираться в лимит 64 байта.
    """
    kb = InlineKeyboardMarkup(row_width=1)

    for idx, route in enumerate(routes):
        text = f"{route['title']} · {route['distance_km']} км · сложн. {route['difficulty']}"
        callback_data = f"route_sel|{region_code}|{idx}"
        kb.add(InlineKeyboardButton(text=text, callback_data=callback_data))

    return kb


def build_route_detail_keyboard(region_code: str, route_index: int, route: Dict) -> InlineKeyboardMarkup:
    """
    Клавиатура под карточкой маршрута:
    - Открыть карту (только если map_url валидный URL)
    - Скачать GPX (если gpx_url валидный URL)
    - Продолжить подбор снаряжения
    """
    kb = InlineKeyboardMarkup(row_width=1)

    map_url = route.get("map_url", "")
    gpx_url = route.get("gpx_url", "")

    if _is_valid_url(map_url):
        kb.add(
            InlineKeyboardButton(
                text="🗺 Открыть карту",
                url=map_url,
            )
        )

    if _is_valid_url(gpx_url):
        kb.add(
            InlineKeyboardButton(
                text="📥 Скачать GPX",
                url=gpx_url,
            )
        )

    kb.add(
        InlineKeyboardButton(
            text="🎒 Продолжить подбор снаряжения",
            callback_data=f"route_gear|{region_code}|{route_index}",
        )
    )

    return kb
