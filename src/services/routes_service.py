from typing import List, Dict, Optional
import os

import pandas as pd

from config import DATA_DIR


# Соответствие кода региона -> CSV-файл
REGION_FILE_MAP = {
    "smolensk_crt67": "routes_smolensk_crt67.csv",
    "russia": "routes_russia.csv",
    "latvia": "routes_latvia.csv",
    "world": "routes_world.csv",
}


def _get_csv_path(region_code: str) -> str:
    filename = REGION_FILE_MAP.get(region_code)
    if not filename:
        raise ValueError(f"Неизвестный код региона: {region_code}")
    return os.path.join(DATA_DIR, filename)


def _load_routes_df(region_code: str) -> pd.DataFrame:
    """
    Загружаем CSV для региона в DataFrame.
    """
    csv_path = _get_csv_path(region_code)

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Файл маршрутов не найден: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8")
    # Гарантируем наличие обязательных колонок
    required_cols = [
        "route_id",
        "title",
        "region",
        "country",
        "distance_km",
        "duration_days",
        "difficulty",
        "season",
        "map_url",
        "gpx_url",
        "description_short",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"В файле {csv_path} отсутствуют колонки: {', '.join(missing)}")

    return df


def _row_to_route(row: pd.Series) -> Dict:
    """
    Преобразование строки DataFrame в удобный словарь.
    """
    return {
        "route_id": str(row["route_id"]),
        "title": str(row["title"]),
        "region": str(row["region"]),
        "country": str(row["country"]),
        "distance_km": float(row["distance_km"]),
        "duration_days": int(row["duration_days"]),
        "difficulty": str(row["difficulty"]),
        "season": str(row["season"]),
        "map_url": str(row["map_url"]) if not pd.isna(row["map_url"]) else "",
        "gpx_url": str(row["gpx_url"]) if not pd.isna(row["gpx_url"]) else "",
        "description_short": str(row["description_short"]),
    }


def get_routes_by_region(region_code: str) -> List[Dict]:
    """
    Возвращает список маршрутов для заданного региона в виде словарей.
    Порядок маршрутов важен — индекс будет использоваться в callback_data.
    """
    df = _load_routes_df(region_code)
    return [_row_to_route(r) for _, r in df.iterrows()]


def get_route_by_index(region_code: str, index: int) -> Optional[Dict]:
    """
    Возвращает один маршрут по его порядковому индексу в таблице.
    Используется для callback-кнопок, чтобы не передавать длинные route_id.
    """
    df = _load_routes_df(region_code)
    if index < 0 or index >= len(df):
        return None
    row = df.iloc[index]
    return _row_to_route(row)
