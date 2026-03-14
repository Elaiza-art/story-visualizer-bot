from aiogram import Router, types, F
from aiogram.filters import Command
from services.api_client import api_client
from keyboards.inline import get_main_menu
import logging

router = Router()
logger = logging.getLogger(__name__)

# для показа избранного
@router.message(Command("favorites"))
async def cmd_favorites(message: types.Message):

    telegram_id = message.from_user.id

    # Проверка доступа
    user = await api_client.check_user_access(telegram_id)
    if not user or not user.get('is_approved', False):
        await message.answer("⏳ Ваш доступ ещё не одобрен")
        return

    # Получаем избранное
    favorites = await api_client.get_favorites(telegram_id)

    if not favorites:
        await message.answer(
            "⭐ <b>Избранное пусто</b>\n\n"
            "Добавляйте проекты в избранное:\n"
            "1️⃣ Откройте /history\n"
            "2️⃣ Нажмите ⭐ рядом с проектом\n\n"
            "Или вручную: <code>/addfav PROJECT_ID</code>",
            reply_markup=get_main_menu()
        )
        return

    # Формируем сообщение
    text = f"⭐ <b>Ваши избранные проекты</b> ({len(favorites)})\n\n"

    for i, project in enumerate(favorites, 1):
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

    # Кнопки для удаления из избранного
    for project in favorites:
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"❌ Удалить #{project['id']}",
                callback_data=f"remove_favorite_{project['id']}"
            )
        ])

    keyboard.append([
        types.InlineKeyboardButton(text="🔙 В меню", callback_data="go_to_menu_fav")
    ])

    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(text, reply_markup=reply_markup)

# Удаление проекта из избранного
@router.callback_query(F.data.startswith("remove_favorite_"))
async def callback_remove_favorite(callback: types.CallbackQuery):

    project_id = int(callback.data.split("_")[-1])
    telegram_id = callback.from_user.id

    from database import remove_from_favorites
    success = remove_from_favorites(telegram_id, project_id)

    if success:
        await callback.answer(f"✅ Проект #{project_id} удалён из избранного")
        await callback.message.delete()
        await cmd_favorites(callback.message)
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "go_to_menu_fav")
async def callback_go_to_menu_fav(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu()
    )
    await callback.answer()


# Команда для добавления в избранное (по ID проекта)
@router.message(Command("addfav"))
async def cmd_add_favorite(message: types.Message):
    telegram_id = message.from_user.id

    try:
        # /addfav 123
        project_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Используйте: <code>/addfav PROJECT_ID</code>\n"
            "Пример: <code>/addfav 123</code>\n\n"
            "ID проекта можно узнать в /history"
        )
        return

    # Проверка доступа
    user = await api_client.check_user_access(telegram_id)
    if not user or not user.get('is_approved', False):
        await message.answer("⏳ Ваш доступ ещё не одобрен")
        return

    # Добавление в избранное
    from database import add_to_favorites
    success = add_to_favorites(telegram_id, project_id)

    if success:
        await message.answer(f"✅ Проект #{project_id} добавлен в избранное!")
    else:
        await message.answer(
            f"Не удалось добавить проект #{project_id}\n\n"
            "Возможно, он уже в избранном или не существует."
        )