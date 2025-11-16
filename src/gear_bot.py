import logging

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.start import register_start_handlers
from handlers.location_menu import register_location_handlers
from handlers.route_flow import register_route_flow_handlers
from handlers.gear_flow import register_gear_flow_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)


def main() -> None:
    # Инициализация бота и диспетчера с FSM-хранилищем
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())

    # Регистрация хендлеров
    register_start_handlers(dp)
    register_location_handlers(dp)
    register_route_flow_handlers(dp)
    register_gear_flow_handlers(dp)

    print("\n================= Gear Checklist Bot =================")
    print("Бот успешно запущен! 🚀")
    print("Теперь можешь открыть Telegram и отправить /start.")
    print("\nКак остановить бота:")
    print("👉 Нажми Ctrl + C в этом окне PowerShell.")
    print("=====================================================\n")

    logging.info("Starting Gear Checklist Bot...")
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
