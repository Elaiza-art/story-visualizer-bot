from aiogram import Router, types, F
from aiogram.filters import Command
from database import get_pending_users, approve_user, get_user_by_telegram_id
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("admin_users"))
# для получения списка пользователей на одобрение
async def cmd_admin_users(message: types.Message):

    telegram_id = message.from_user.id

    # Проверяем, админ ли
    user = get_user_by_telegram_id(telegram_id)
    if not user or not user.get('is_admin', False):
        await message.answer("У вас нет прав администратора")
        return

    # Получаем список ожидающих
    pending_users = get_pending_users()

    if not pending_users:
        await message.answer("Нет пользователей, ожидающих одобрения...")
        return

    # Сообшение о новых пользователях
    text = "🔔 <b>Пользователи на модерации:</b>\n\n"

    for i, u in enumerate(pending_users, 1):
        text += f"{i}. 👤 {u['full_name'] or 'Без имени'}\n"
        text += f"   ID: <code>{u['telegram_id']}</code>\n"
        text += f"   Username: @{u['username'] or 'нет'}\n\n"

    text += "<i>Для одобрения: /approve USER_ID</i>"

    await message.answer(text)


@router.message(Command("approve"))
# функция для одобрения
async def cmd_approve(message: types.Message):
    telegram_id = message.from_user.id

    admin = get_user_by_telegram_id(telegram_id)
    if not admin or not admin.get('is_admin', False):
        await message.answer("У вас нет прав администратора")
        return

    # Получаем ID пользователя для одобрения
    try:
        user_id_to_approve = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Используйте: <code>/approve USER_ID</code>\n"
            "Пример: <code>/approve 123456789</code>"
        )
        return

    # Одобряем
    if approve_user(user_id_to_approve):
        await message.answer(f"✅ Пользователь {user_id_to_approve} одобрен!")

        # уведомление пользователя об одобрении
        try:
            await message.bot.send_message(
                user_id_to_approve,
                "🎉 <b>Ваш доступ одобрен!</b>\n\n"
                "Теперь вы можете использовать бота.\n\n"
                "Нажмите /start для начала работы."
            )
            logger.info(f"Уведомление отправлено пользователю {user_id_to_approve}")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление: {e}")
            await message.answer("Пользователь одобрен, но уведомление не отправлено (возможно, бот заблокирован)")
    else:
        await message.answer(f"Не удалось одобрить пользователя {user_id_to_approve}")


# функция для отображения статистики
@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: types.Message):
    telegram_id = message.from_user.id

    user = get_user_by_telegram_id(telegram_id)
    if not user or not user.get('is_admin', False):
        await message.answer("❌ У вас нет прав администратора")
        return

    from database import get_all_users
    all_users = get_all_users()

    approved_count = sum(1 for u in all_users if u['is_approved'])
    pending_count = sum(1 for u in all_users if not u['is_approved'])
    admin_count = sum(1 for u in all_users if u['is_admin'])

    text = "📊 <b>Статистика бота</b>\n\n"
    text += f"👥 Всего пользователей: {len(all_users)}\n"
    text += f"✅ Одобрено: {approved_count}\n"
    text += f"⏳ На модерации: {pending_count}\n"
    text += f"👑 Админов: {admin_count}\n"

    await message.answer(text)