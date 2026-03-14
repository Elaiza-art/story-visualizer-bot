from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from services.api_client import api_client
import logging
from keyboards.inline import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    logger.info(f"/start от пользователя {telegram_id} (@{username})")
    wait_message = await message.answer("⏳ Проверяю доступ...")

    try:
        user_data = await api_client.register_user(
            telegram_id=telegram_id,
            username=f"@{username}" if username else full_name
        )
        if user_data is None:
            await wait_message.delete()
            await message.answer(
                "❌ <b>Ошибка подключения</b>\n\n"
                "Не удалось связаться с сервером. Попробуйте позже."
            )
            return

        is_approved = user_data.get("is_approved", False)
        is_admin = user_data.get("is_admin", False)

        try:
            await wait_message.delete()
        except Exception:
            pass

        if not is_approved:
            # Доступ не одобрен
            await message.answer(
                f"👋 <b>Привет, {full_name}!</b>\n\n"
                "⏳ <b>Ваш доступ на модерации</b>\n\n"
                "Администратор должен одобрить вашу заявку. "
                "Вы получите уведомление, когда доступ будет открыт.\n\n"
            )

            try:
                from config import config
                if config.ADMIN_ID:
                    await message.bot.send_message(
                        config.ADMIN_ID,
                        f"🔔 <b>Новый пользователь!</b>\n\n"
                        f"ID: <code>{telegram_id}</code>\n"
                        f"Имя: {full_name}\n"
                        f"Username: @{username or 'нет'}\n\n"
                        f"Требуется одобрение."
                    )
            except Exception as e:
                logger.error(f"Не удалось уведомить админа: {e}")

            return

        welcome_text = (
            f"✅ <b>Добро пожаловать, {full_name}!</b>\n\n"
            "🎬 <b>Визуализатор Рассказов</b>\n\n"
            "Отправьте текст истории, и я создам по нему видео!\n\n"
            "Используйте команды:"
        )

        await message.answer(
            welcome_text,
            reply_markup=get_main_menu()
        )

    except Exception as e:
        logger.error(f"Ошибка в /start: {e}", exc_info=True)
        try:
            await wait_message.delete()
        except Exception:
            pass
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Попробуйте позже или обратитесь к администратору."
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