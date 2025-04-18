import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers import orders
from config import config
from database import init_db
from handlers import main_menu, products, finance, family, settings

# Инициализация базы данных
init_db()

# Создаём экземпляр бота ОДИН РАЗ
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Основная асинхронная функция
async def main():
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем все маршруты (обработчики)
    dp.include_routers(
        main_menu.router,
        products.router,
        finance.router,
        family.router,
        orders.router,
    )

    print("✅ Бот запущен")
    await dp.start_polling(bot)

# Точка входа
if __name__ == "__main__":
    asyncio.run(main())