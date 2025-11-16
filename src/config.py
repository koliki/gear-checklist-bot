import os
from dotenv import load_dotenv

# Путь к корню проекта: .../gear-checklist-bot
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Директории данных и ассетов
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
QR_TEMP_DIR = os.path.join(ASSETS_DIR, "qr_temp")

# Гарантируем существование папки для временных QR-кодов
os.makedirs(QR_TEMP_DIR, exist_ok=True)

# Загружаем переменные окружения из .env в корне проекта
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Убедись, что файл .env создан и в нём задан BOT_TOKEN.")
