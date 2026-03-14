from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from states.forms import StoryInput
from services.api_client import api_client
from keyboards.inline import get_main_menu
import logging
import re

router = Router()
logger = logging.getLogger(__name__)

NEW_PROJECT_BUTTON = "📝 Новый проект"


@router.message(F.text == NEW_PROJECT_BUTTON)
async def cmd_new_project(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    user = await api_client.check_user_access(telegram_id)
    if not user or not user.get('is_approved', False):
        await message.answer("⏳ Ваш доступ ещё не одобрен")
        return

    # Инструкция пользователю
    await message.answer(
        "📝 <b>Отправь текст своей истории</b>\n\n"
        "✨ <b>Советы:</b>\n"
        "• Минимум 100 символов для истории\n"
        "• Максимум 5000 символов (если больше — разбей на части)\n"
        "• Чем детальнее описание, тем лучше результат!\n\n"
        "🔙 Чтобы отменить, напиши /cancel",
        reply_markup=types.ReplyKeyboardRemove()
    )

    # Переход в состояние ожидания текста
    await state.set_state(StoryInput.waiting_for_text)
    await state.update_data({"telegram_id": telegram_id})


# обработка текста
@router.message(StoryInput.waiting_for_text, F.text)
async def process_story_text(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if text.lower() in ['/cancel', 'отмена', 'отменить']:
        await state.clear()
        await message.answer(
            "❌ Ввод отменён",
            reply_markup=get_main_menu()
        )
        return

    # проверка требований к тексту
    if len(text) < 100:
        await message.answer(
            "❌ <b>Текст слишком короткий</b>\n\n"
            "Пожалуйста, отправь историю минимум из 100 символов.\n"
            "Или напиши /cancel для отмены."
        )
        return

    if len(text) > 5000:
        await message.answer(
            "❌ <b>Текст слишком длинный</b>\n\n"
            "Максимум 5000 символов. Пожалуйста, разбей историю на части "
            "или сократи её.\n"
            "Или напиши /cancel для отмены."
        )
        return

    data = await state.get_data()
    telegram_id = data.get("telegram_id")

    wait_msg = await message.answer("⏳ Сохраняю проект...")

    try:
        # Создаём проект через API/БД
        project = await api_client.create_project(
            telegram_id=telegram_id,
            text=text,
            title="Без названия"  # позже добавлю авто-генерацию заголовка
        )

        await wait_msg.delete()

        if project:
            await message.answer(
                "✅ <b>Проект создан!</b>\n\n"
                f"🆔 ID проекта: <code>{project['id']}</code>\n\n"
                "🔄 Запускаю генерацию...\n"
                "Проверить статус: /status",
                reply_markup=get_main_menu()
            )

            # TODO: добавлю запуск генерации в фоне потом
            # await start_generation(project['id'])

        else:
            await message.answer(
                "❌ <b>Ошибка сохранения</b>\n\n"
                "Не удалось создать проект. Попробуйте позже.",
                reply_markup=get_main_menu()
            )

    except Exception as e:
        logger.error(f"Ошибка при создании проекта: {e}", exc_info=True)
        await wait_msg.delete()
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            reply_markup=get_main_menu()
        )

    finally:
        await state.clear()


@router.message(Command("cancel"), StateFilter(StoryInput.waiting_for_text))
@router.message(F.text.lower() == "отмена", StateFilter(StoryInput.waiting_for_text))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Ввод отменён",
        reply_markup=get_main_menu()
    )