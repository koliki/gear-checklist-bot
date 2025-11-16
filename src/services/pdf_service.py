from io import BytesIO
import os
from typing import Dict, List, Tuple

import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

from config import FONTS_DIR, QR_TEMP_DIR


def _font_path() -> str:
    path = os.path.join(FONTS_DIR, "DejaVuSans.ttf")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Файл шрифта DejaVuSans.ttf не найден по пути: {path}. "
            f"Скачай DejaVuSans.ttf и положи его в каталог assets/fonts/."
        )
    return path


def _register_font():
    """
    Регистрируем шрифт DejaVuSans для поддержки кириллицы.
    """
    font_path = _font_path()
    try:
        pdfmetrics.getFont("DejaVu")
    except KeyError:
        pdfmetrics.registerFont(TTFont("DejaVu", font_path))


def _is_valid_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    url = url.strip()
    return url.startswith("http://") or url.startswith("https://")


def _create_qr_image(target_url: str) -> str:
    os.makedirs(QR_TEMP_DIR, exist_ok=True)
    filename = f"qr_{os.urandom(4).hex()}.png"
    path = os.path.join(QR_TEMP_DIR, filename)

    qr = qrcode.QRCode(
        version=2,
        box_size=4,
        border=1,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)

    return path


def generate_gear_pdf(
    route: Dict,
    participants: int,
    days: int,
    season_human: str,
    experience_human: str,
    gear: Dict[str, List[Dict]],
    region_notes: str,
) -> Tuple[bytes, str]:
    """
    Генерация PDF-чек-листа на основе ReportLab.
    Поддерживает кириллицу, показывает:
    - инфо о маршруте и параметрах похода
    - особенности региона
    - групповой и личный список снаряжения
    - QR-код маршрута на отдельной странице (если есть ссылка)
    """

    _register_font()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = 25 * mm
    bottom_margin = 20 * mm

    x = left_margin
    y = height - top_margin
    line_height = 6 * mm

    def draw_line(text: str, font_size: int = 11):
        nonlocal x, y
        if y < bottom_margin:
            c.showPage()
            y = height - top_margin
            c.setFont("DejaVu", font_size)

        c.setFont("DejaVu", font_size)
        c.drawString(x, y, text)
        y -= line_height

    # ---------- Заголовок ----------
    c.setFont("DejaVu", 18)
    c.drawString(x, y, "Чек-лист снаряжения")
    y -= line_height * 1.5

    # ---------- Информация о маршруте ----------
    title = str(route.get("title", "Маршрут"))
    region = str(route.get("region", "Регион"))
    country = str(route.get("country", "Страна"))
    distance = route.get("distance_km", "")
    distance_text = f"{distance} км" if distance != "" else ""

    draw_line(f"Маршрут: {title}", font_size=13)
    if distance_text:
        draw_line(f"Регион: {region}, страна: {country}, дистанция: {distance_text}")
    else:
        draw_line(f"Регион: {region}, страна: {country}")
    draw_line(f"Участников: {participants}, длительность: {days} дн.")
    draw_line(f"Сезон: {season_human}, опыт группы: {experience_human}")
    y -= line_height

    # ---------- Особенности региона ----------
    if region_notes:
        draw_line("Особенности региона:", font_size=12)
        # разбиваем длинный текст на строки по ширине страницы
        max_width = width - left_margin - right_margin
        lines = simpleSplit(region_notes, "DejaVu", 10, max_width)
        for line in lines:
            draw_line(line, font_size=10)
        y -= line_height / 2

    # ---------- Групповое снаряжение ----------
    draw_line("Групповое снаряжение:", font_size=12)
    group_items = gear.get("group", [])
    if group_items:
        for item in group_items:
            name = str(item["name"])
            category = str(item["category"])
            qty = item.get("quantity", 1)
            line = f"[ ] {name} ({category}) — {qty} шт."
            # переносим длинные строки
            max_width = width - left_margin - right_margin
            lines = simpleSplit(line, "DejaVu", 10, max_width)
            for l in lines:
                draw_line(l, font_size=10)
    else:
        draw_line("Нет обязательного группового снаряжения.", font_size=10)
    y -= line_height / 2

    # ---------- Личное снаряжение ----------
    draw_line("Личное снаряжение (на каждого участника):", font_size=12)
    personal_items = gear.get("personal", [])
    if personal_items:
        for item in personal_items:
            name = str(item["name"])
            category = str(item["category"])
            qty = item.get("quantity_per_person", 1)
            line = f"[ ] {name} ({category}) — {qty} шт. на человека"
            max_width = width - left_margin - right_margin
            lines = simpleSplit(line, "DejaVu", 10, max_width)
            for l in lines:
                draw_line(l, font_size=10)
    else:
        draw_line("Нет обязательного личного снаряжения.", font_size=10)

    # ---------- QR-код на отдельной странице ----------
    target_url = ""
    if _is_valid_url(route.get("map_url", "")):
        target_url = route["map_url"]
    elif _is_valid_url(route.get("gpx_url", "")):
        target_url = route["gpx_url"]

    if target_url:
        try:
            qr_path = _create_qr_image(target_url)
            c.showPage()
            c.setFont("DejaVu", 16)
            c.drawString(left_margin, height - top_margin, "QR-код маршрута")
            qr_size = 50 * mm
            c.drawImage(
                qr_path,
                left_margin,
                height - top_margin - qr_size - 10 * mm,
                width=qr_size,
                height=qr_size,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception as e:
            c.showPage()
            c.setFont("DejaVu", 12)
            c.drawString(left_margin, height - top_margin, f"Не удалось отрисовать QR-код: {e}")

    c.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    safe_title = "".join(ch if ch.isalnum() or ch in " _-" else "_" for ch in title)
    filename = f"gear_{safe_title}.pdf"

    return pdf_bytes, filename
