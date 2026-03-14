from aiogram import Router, types, F
from aiogram.filters import Command
from services.api_client import api_client
from keyboards.inline import get_main_menu
from aiogram.exceptions import TelegramBadRequest
import logging

router = Router()
logger = logging.getLogger(__name__)

PROJECTS_PER_PAGE = 5  # Количество проектов на страницу

# функция для показа истории проектов
@router.message(Command("history"))
async def cmd_history(message: types.Message, page: int = 0):
    telegram_id = message.from_user.id

    # Проверка доступа
    user = await api_client.check_user_access(telegram_id)
    if not user or not user.get('is_approved', False):
        await message.answer("⏳ Ваш доступ ещё не одобрен")
        return

    # Получаем проекты
    projects = await api_client.get_projects(telegram_id, limit=PROJECTS_PER_PAGE + 1)

    if not projects:
        await message.answer(
            "📁 <b>История пуста</b>\n\n"
            "У вас пока нет проектов.\n"
            "Нажмите '📝 Новый проект' для создания!",
            reply_markup=get_main_menu()
        )
        return

    has_next = len(projects) > PROJECTS_PER_PAGE
    if has_next:
        projects = projects[:PROJECTS_PER_PAGE]

    text = f"📁 <b>Ваши проекты</b> (страница {page + 1})\n\n"

    for i, project in enumerate(projects, 1):
        status_emoji = {
            'pending': '⏳',
            'generating': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(project.get('status', 'pending'), '❓')

        text += f"{i}. {status_emoji} <b>{project.get('title', 'Без названия')}</b>\n"
        text += f"   📅 {project.get('created_at', 'N/A')}\n"
        text += f"   🆔 ID: <code>{project.get('id')}</code>\n"
        text += f"   📊 Статус: {project.get('status', 'unknown')}\n\n"

    keyboard = []

    for project in projects:
        project_id = project.get('id')
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"⭐ В избранное #{project_id}",
                callback_data=f"add_favorite_{project_id}"
            )
        ])

    # Кнопки для каждого проекта (скачать)
    for project in projects:
        if project.get('status') == 'completed':
            keyboard.append([
                types.InlineKeyboardButton(
                    text=f"📥 Скачать #{project['id']}",
                    callback_data=f"download_project_{project['id']}"
                )
            ])

    # кнопки для пролистования страниц
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"history_page_{page - 1}"
            )
        )
    if has_next:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=f"history_page_{page + 1}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        types.InlineKeyboardButton(
            text="🔙 В меню",
            callback_data="go_to_menu"
        )
    ])

    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(text, reply_markup=reply_markup)

#Переключение страницы истории
@router.callback_query(F.data.startswith("history_page_"))
async def callback_history_page(callback: types.CallbackQuery):
    
    page = int(callback.data.split("_")[-1])
    await callback.message.delete()
    await cmd_history(callback.message, page=page)
    try:
        await callback.answer()
    except TelegramBadRequest:
        logger.warning("Callback query expired")

#Скачивание проекта
@router.callback_query(F.data.startswith("download_project_"))
async def callback_download_project(callback: types.CallbackQuery):

    project_id = int(callback.data.split("_")[-1])
    telegram_id = callback.from_user.id

    try:
        await callback.answer("⏳ Подготавливаю видео...")
    except TelegramBadRequest:
        logger.warning("Callback query expired")


    # TODO: Здесь будет логика получения файла видео
    # Пока заглушка

    await callback.answer(
        "🚧 Функция скачивания в разработке\n"
        "Видео будет доступно после завершения генерации",
        show_alert=True
    )

# Добавление проекта в избранное по кнопке
@router.callback_query(F.data.startswith("add_favorite_"))
async def callback_add_favorite(callback: types.CallbackQuery):

    project_id = int(callback.data.split("_")[-1])
    telegram_id = callback.from_user.id

    # Добавляем в избранное через БД
    from database import add_to_favorites
    success = add_to_favorites(telegram_id, project_id)

    if success:
        await callback.answer(f"✅ Проект #{project_id} добавлен в избранное! ⭐")
    else:
        await callback.answer("ℹ️Уже в избранном или ошибка", show_alert=False)

    try:
        await callback.answer()
    except TelegramBadRequest:
        logger.warning("Callback query expired")


@router.callback_query(F.data == "go_to_menu")
async def callback_go_to_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu()
    )
    try:
        await callback.answer()
    except TelegramBadRequest:
        logger.warning("Callback query expired")