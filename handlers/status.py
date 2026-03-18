from aiogram import Router, types, F
from aiogram.filters import Command
from services.api_client import api_client
from keyboards.inline import get_main_menu
import logging

router = Router()
logger = logging.getLogger(__name__)

# Статусы для отображения
STATUS_BUTTON = "⏳ Прогресс"

STATUS_EMOJI = {
    'pending': '⏳',
    'generating': '🔄',
    'completed': '✅',
    'failed': '❌'
}

STATUS_TEXT = {
    'pending': 'В очереди на генерацию',
    'generating': 'Идёт генерация',
    'completed': 'Готово',
    'failed': 'Ошибка генерации'
}

# формирует текст статуса и флаг наличия активных проектов
async def get_projects_status_text(telegram_id: int) -> tuple[str, bool]:
    projects = await api_client.get_projects(telegram_id, limit=5)

    if not projects:
        text = ("📁 <b>У вас нет проектов</b>\n\n"
                "Создайте новый проект через команду /new\n"
                "или кнопку '📝 Новый проект'")
        return text, False

    active_projects = [p for p in projects if p.get('status') in ['pending', 'generating']]
    completed_projects = [p for p in projects if p.get('status') == 'completed']

    text = "📊 <b>Статус ваших проектов</b>\n\n"

    # Сначала показываем активные проекты
    if active_projects:
        text += "🔄 <b>В процессе:</b>\n\n"
        for project in active_projects:
            status_emoji = STATUS_EMOJI.get(project.get('status', 'pending'), '❓')
            status_name = STATUS_TEXT.get(project.get('status', 'pending'), 'Неизвестно')

            text += f"{status_emoji} <b>{project.get('title', 'Без названия')}</b>\n"
            text += f"   🆔 ID: <code>{project.get('id')}</code>\n"
            text += f"   📊 Статус: {status_name}\n"

            # Если есть прогресс
            progress = project.get('progress', None)
            if progress:
                text += f"   📈 Прогресс: {progress}\n"

            error = project.get('error_message', None)
            if error:
                text += f"   ❌ Ошибка: {error}\n"

            text += "\n"
    else:
        text += "✅ <b>Активных задач нет</b>\n\n"

    # Показываем последние готовые
    if completed_projects:
        text += "✅ <b>Последние готовые:</b>\n\n"
        for project in completed_projects[:3]:
            text += f"✅ {project.get('title', 'Без названия')}\n"
            text += f"   📅 {project.get('completed_at', 'N/A')}\n"
            text += f"   🆔 ID: <code>{project.get('id')}</code>\n\n"

    return text, bool(active_projects)

# создает клавиатуру для статуса
def get_status_keyboard(has_active_projects: bool) -> types.InlineKeyboardMarkup:

    keyboard = []

    if has_active_projects:
        keyboard.append([
            types.InlineKeyboardButton(
                text="🔄 Обновить статус",
                callback_data="refresh_status"
            )
        ])

    keyboard.append([
        types.InlineKeyboardButton(
            text="🔙 В меню",
            callback_data="go_to_menu_status"
        )
    ])

    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

# Показывает статус текущих проектов пользователя
@router.message(Command("status"))
@router.message(F.text == STATUS_BUTTON)
async def cmd_status(message: types.Message):
    telegram_id = message.from_user.id

    user = await api_client.check_user_access(telegram_id)
    if not user or not user.get('is_approved', False):
        await message.answer("⏳ Ваш доступ ещё не одобрен")
        return

    text, has_active = await get_projects_status_text(telegram_id)
    reply_markup = get_status_keyboard(has_active)

    await message.answer(text, reply_markup=reply_markup)

# Обновление статуса проектов
@router.callback_query(F.data == "refresh_status")
async def callback_refresh_status(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    await callback.answer("🔄 Обновляю статус...")

    text, has_active = await get_projects_status_text(telegram_id)
    reply_markup = get_status_keyboard(has_active)

    await callback.message.edit_text(text, reply_markup=reply_markup)


@router.callback_query(F.data == "go_to_menu_status")
async def callback_go_to_menu_status(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await callback.message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu()
    )
    await callback.answer()
