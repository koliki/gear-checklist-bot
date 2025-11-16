from typing import List, Dict
import os
import math

import pandas as pd

from config import DATA_DIR


def _gear_csv_path() -> str:
    return os.path.join(DATA_DIR, "gear_db.csv")


def _location_csv_path() -> str:
    return os.path.join(DATA_DIR, "location_gear.csv")


def _load_gear_df() -> pd.DataFrame:
    path = _gear_csv_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл снаряжения не найден: {path}")

    df = pd.read_csv(path, encoding="utf-8")
    required_cols = [
        "item_id",
        "category",
        "name",
        "is_personal",
        "season",
        "min_days",
        "max_days",
        "experience_level",
        "mandatory",
        "quantity_per_person",
        "quantity_group",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"В файле {path} отсутствуют колонки: {', '.join(missing)}")
    return df


def _parse_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _season_match(item_season: str, user_season: str) -> bool:
    """
    Простое сопоставление сезона.
    all/any — подходит всегда
    summer, winter — только для соответствующего сезона
    mid — для весны/осени
    """
    item_season = str(item_season).strip().lower()
    user_season = str(user_season).strip().lower()

    if item_season in ("", "all", "any"):
        return True
    if item_season == "summer" and user_season == "summer":
        return True
    if item_season == "winter" and user_season == "winter":
        return True
    if item_season in ("mid", "mid_season", "shoulder") and user_season in ("spring", "autumn"):
        return True
    if item_season == user_season:
        return True
    return False


def _days_match(min_days, max_days, user_days: int) -> bool:
    min_d = _parse_int(min_days, 1)
    max_d = _parse_int(max_days, 0)
    if user_days < min_d:
        return False
    if max_d and user_days > max_d:
        return False
    return True


def _experience_match(item_level: str, user_level: str) -> bool:
    item_level = str(item_level).strip().lower()
    user_level = str(user_level).strip().lower()
    if item_level in ("", "any"):
        return True
    return item_level == user_level


def get_region_notes(region_code: str) -> str:
    """
    Возвращает текстовые рекомендации по региону (если есть).
    """
    path = _location_csv_path()
    if not os.path.exists(path):
        return ""

    df = pd.read_csv(path, encoding="utf-8")
    if "region_code" not in df.columns or "extra_notes" not in df.columns:
        return ""

    row = df.loc[df["region_code"] == region_code]
    if row.empty:
        return ""

    note = str(row.iloc[0]["extra_notes"])
    return note.strip()


def _calc_group_quantity(item_id: str, base_qty: int, participants: int, days: int) -> int:
    """
    Небольшая «умная» логика количества для некоторых групповых предметов.
    Остальные — по количеству из CSV.
    """
    item_id = str(item_id)

    # Палатки: 3-местные, считаем по людям
    if item_id == "tent_3p":
        return max(1, math.ceil(participants / 3))

    # Газовые баллоны: примерно 1 баллон на 2х человек на каждые 2 дня
    if item_id == "gas_can":
        groups_by_people = max(1, math.ceil(participants / 2))
        groups_by_days = max(1, math.ceil(days / 2))
        return groups_by_people * groups_by_days

    # По умолчанию — то, что указано в CSV
    return max(1, base_qty)


def generate_gear_list(
    region_code: str,
    participants: int,
    days: int,
    season: str,
    experience_level: str,
) -> Dict[str, List[Dict]]:
    """
    Возвращает словарь с двумя списками:
    - group: групповое снаряжение
    - personal: личное снаряжение
    Каждая запись: {category, name, quantity/quantity_per_person, mandatory, is_personal}
    """
    df = _load_gear_df()

    group_items: List[Dict] = []
    personal_items: List[Dict] = []

    for _, row in df.iterrows():
        if not _season_match(row["season"], season):
            continue
        if not _days_match(row["min_days"], row["max_days"], days):
            continue
        if not _experience_match(row["experience_level"], experience_level):
            continue

        is_personal = _parse_int(row["is_personal"], 1) == 1
        mandatory = str(row["mandatory"]).strip().lower() in ("yes", "1", "true")

        if is_personal:
            qty_per_person = _parse_int(row["quantity_per_person"], 1)
            item = {
                "item_id": str(row["item_id"]),
                "category": str(row["category"]),
                "name": str(row["name"]),
                "is_personal": True,
                "quantity_per_person": qty_per_person,
                "mandatory": mandatory,
            }
            personal_items.append(item)
        else:
            base_qty = _parse_int(row["quantity_group"], 1)
            qty = _calc_group_quantity(
                item_id=row["item_id"],
                base_qty=base_qty,
                participants=participants,
                days=days,
            )
            item = {
                "item_id": str(row["item_id"]),
                "category": str(row["category"]),
                "name": str(row["name"]),
                "is_personal": False,
                "quantity": qty,
                "mandatory": mandatory,
            }
            group_items.append(item)

    return {
        "group": group_items,
        "personal": personal_items,
    }
