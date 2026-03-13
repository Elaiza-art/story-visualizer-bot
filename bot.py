import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart

from config import config
from handlers import start, generate, status, history, favorites, admin

# Настройка логов
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_bot() -> Bot:
    return Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_dispatcher() -> Dispatcher:

    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(generate.router)
    dp.include_router(status.router)
    dp.include_router(history.router)
    dp.include_router(favorites.router)
    dp.include_router(admin.router)

    return dp


async def on_startup(bot: Bot):

    logger.info("🤖 Бот запущен!")

    bot_info = await bot.get_me()
    logger.info(f"Бот: @{bot_info.username} (ID: {bot_info.id})")

    # команды меню (пока заглушка)
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Справка"),
        types.BotCommand(command="new", description="Создать проект"),
        types.BotCommand(command="status", description="Статус генерации"),
        types.BotCommand(command="history", description="История проектов"),
        types.BotCommand(command="favorites", description="Избранное"),
    ])
    logger.info("Команды меню установлены!")


async def on_shutdown(bot: Bot):

    logger.info("Бот остановлен!!!")
    await bot.session.close()


async def main():

    bot = create_bot()
    dp = create_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("🔄 Запускаем поллинг...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚡ Остановка по Ctrl+C")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)