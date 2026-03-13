from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):

    await message.answer(
        "👋 Привет! Я бот <b>Визуализатор Рассказов</b> 🎬\n\n"
        "Доступные команды:\n"
        "/help — Справка\n"
        "/new — Создать новый проект\n"
        "/history — Мои проекты\n"
        "/favorites — Избранное"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "📚 <b>Справка по боту</b>\n\n"
        "🎬 <b>Визуализатор Рассказов</b> — создаёт видео по тексту.\n\n"
        "<b>Команды:</b>\n"
        "/start — Запустить бота заново\n"
        "/new — Отправить текст истории для визуализации\n"
        "/status — Проверить статус генерации\n"
        "/history — Посмотреть историю проектов\n"
        "/favorites — Управление избранным\n"
        "/help — Эта справка"
    )