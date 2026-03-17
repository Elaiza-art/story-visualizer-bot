from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.forms import StoryInput
from services.api_client import api_client
from keyboards.inline import get_main_menu, get_content_type_keyboard, get_model_keyboard, get_cancel_keyboard
import logging

router = Router()
logger = logging.getLogger(__name__)


# шаблоны

NEW_PROJECT_BUTTON = "📝 Новый проект"

AVAILABLE_MODELS = {
    'comfyui': {
        'name': 'ComfyUI (Stable Diffusion)',
        'emoji': '🎨',
        'description': 'Генерация изображений и видео',
    },
    'qwen': {
        'name': 'Qwen',
        'emoji': '🤖',
        'description': 'Генерация изображений и видео',
    }
}

CONTENT_TYPES = {
    'content_type_image': 'image',
    'content_type_video': 'video'
}

MODELS = {
    'model_comfyui': 'comfyui',
    'model_qwen': 'qwen'
}

SUCCESS_TEMPLATES = {
    'image': {
        'emoji': '🖼',
        'type_name': 'Изображение'
    },
    'video': {
        'emoji': '🎬',
        'type_name': 'Видео'
    }
}

TEXT_LIMITS = {
    'image': {'min': 50, 'max': 5000},
    'video': {'min': 100, 'max': 5000}
}

# ф - ии для вывода вспомогательного текста

def get_content_type_text() -> str:
    return (
        "🎯 <b>Что будем создавать?</b>\n\n"
        "🖼️ <b>Только изображение</b> — одна иллюстрация по описанию\n"
        "🎬 <b>Видео</b> — слайд - шоу или видео\n\n"
        "Выберите тип контента:"
    )


def get_models_text() -> str:
    text = "🤖 <b>Выберите модель для генерации</b>\n\n"
    for model_id, model_info in AVAILABLE_MODELS.items():
        text += f"{model_info['emoji']} <b>{model_info['name']}</b>\n"
        text += f"   • {model_info['description']}\n"
    text += "Выберите модель:"
    return text


def get_text_input_prompt(content_type: str) -> str:
    limits = TEXT_LIMITS.get(content_type, TEXT_LIMITS['video'])

    if content_type == "image":
        return (
            "🖼 <b>Отправьте описание изображения</b>\n\n"
            "✨ <b>Советы:</b>\n"
            f"• Минимум {limits['min']} символов\n"
            f"• Максимум {limits['max']} символов\n"
            "• Опишите детали: персонажи, фон, стиль, освещение\n\n"
            "🔙 Чтобы отменить, напишите /cancel"
        )
    return (
        "🎬 <b>Отправьте текст своей истории</b>\n\n"
        "✨ <b>Советы:</b>\n"
        f"• Минимум {limits['min']} символов для хорошей сегментации\n"
        f"• Максимум {limits['max']} символов (если больше — разбей на части)\n"
        "• Чем детальнее описание, тем лучше результат!\n\n"
        "🔙 Чтобы отменить, напишите /cancel"
    )


def get_success_message(content_type: str, model: str, text: str, project_id: int) -> str:
    template = SUCCESS_TEMPLATES.get(content_type, SUCCESS_TEMPLATES['video'])
    model_name = AVAILABLE_MODELS.get(model, {}).get('name', 'Unknown')

    return (
        f"✅ <b>Проект создан!</b>\n\n"
        f"{template['emoji']} <b>Тип:</b> {template['type_name']}\n"
        f"🤖 <b>Модель:</b> {model_name}\n"
        f"🆔 <b>ID проекта:</b> <code>{project_id}</code>\n\n"
        "🔄 Запускаю генерацию...\n"
        "Проверить статус: /status"
    )


# обработчики

@router.message(F.text == NEW_PROJECT_BUTTON)
async def cmd_new_project(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    # Проверяем доступ пользователя
    user = await api_client.check_user_access(telegram_id)
    if not user or not user.get('is_approved', False):
        await message.answer("⏳ Ваш доступ ещё не одобрен")
        return
    await state.update_data(telegram_id=telegram_id)

    await message.answer(
        get_content_type_text(),
        reply_markup=get_content_type_keyboard()
    )
    await state.set_state(StoryInput.choosing_content_type)


@router.callback_query(F.data.in_(CONTENT_TYPES.keys()))
async def callback_content_type(callback: types.CallbackQuery, state: FSMContext):
    content_type = CONTENT_TYPES[callback.data]

    await state.update_data(content_type=content_type)

    type_name = SUCCESS_TEMPLATES[content_type]['type_name']
    await callback.answer(f"Выбрано: {type_name}")
    await callback.message.delete()

    await callback.message.answer(
        get_models_text(),
        reply_markup=get_model_keyboard()
    )

    await state.set_state(StoryInput.choosing_model)


@router.callback_query(F.data.in_(MODELS.keys()))
async def callback_model(callback: types.CallbackQuery, state: FSMContext):
    model = MODELS[callback.data]
    await state.update_data(model=model)

    model_name = AVAILABLE_MODELS.get(model, {}).get('name', 'Unknown')
    await callback.answer(f"Выбрана модель: {model_name}")

    await callback.message.delete()

    data = await state.get_data()
    content_type = data.get("content_type", "video")

    await callback.message.answer(
        get_text_input_prompt(content_type),
        reply_markup=get_cancel_keyboard()
    )

    await state.set_state(StoryInput.waiting_for_text)

# кнопка отмены
@router.callback_query(F.data == "cancel_creation")
async def callback_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Создание проекта отменено",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "❌ Создание проекта отменено",
        reply_markup=get_main_menu()
    )


@router.message(StoryInput.waiting_for_text, F.text)
async def process_story_text(message: types.Message, state: FSMContext):
    text = message.text.strip()

    data = await state.get_data()

    # проверка наличия обязательных полей
    required_fields = ['telegram_id', 'content_type', 'model']
    if not all(field in data for field in required_fields):
        logger.warning(f"Missing required fields in state: {data}")
        await state.clear()
        await message.answer(
            "❌ Ошибка данных. Начните создание проекта заново.",
            reply_markup=get_main_menu()
        )
        return

    telegram_id = data["telegram_id"]
    content_type = data["content_type"]
    model = data["model"]

    if data.get('processing', False):
        await message.answer("⏳ Предыдущий запрос уже обрабатывается...")
        return

    # Устанавливаем флаг обработки
    await state.update_data(processing=True)

    # Валидация текста
    limits = TEXT_LIMITS.get(content_type, TEXT_LIMITS['video'])

    if len(text) < limits['min']:
        await message.answer(
            f"❌ <b>Текст слишком короткий</b>\n\n"
            f"Пожалуйста, отправьте текст минимум из {limits['min']} символов.\n"
            f"Сейчас: {len(text)} символов.\n"
            "Или напишите /cancel для отмены."
        )
        return

    if len(text) > limits['max']:
        await message.answer(
            f"❌ <b>Текст слишком длинный</b>\n\n"
            f"Максимум {limits['max']} символов. Пожалуйста, сократите текст.\n"
            f"Сейчас: {len(text)} символов.\n"
            "Или напишите /cancel для отмены."
        )
        return

    model_name = AVAILABLE_MODELS.get(model, {}).get('name', 'Unknown')
    type_name = SUCCESS_TEMPLATES[content_type]['type_name']

    wait_msg = await message.answer(
        f"⏳ <b>Создаю проект...</b>\n\n"
        f"🎯 Тип: {type_name}\n"
        f"🤖 Модель: {model_name}\n\n"
        "🔄 Это может занять несколько минут..."
    )

    try:
        # Создаём проект
        title = text[:50] + "..." if len(text) > 50 else text

        project = await api_client.create_project(
            telegram_id=telegram_id,
            text=text,
            title=title,
            content_type=content_type,
            model=model
        )

        await wait_msg.delete()

        if project:
            await message.answer(
                get_success_message(content_type, model, text, project['id']),
                reply_markup=get_main_menu()
            )
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