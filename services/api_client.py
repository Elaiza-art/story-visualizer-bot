import logging

from typing import Optional, Dict, Any
from database import (
    get_user_by_telegram_id,
    register_user as db_register_user,
    approve_user,
    get_pending_users,
    get_all_users,
    get_user_projects,
    update_project_status,
    add_to_favorites,
    get_user_favorites,
    create_project as db_create_project
)

logger = logging.getLogger(__name__)


class APIClient:

    def __init__(self, mode: str = "local"):
        self.mode = mode  # "local" или "remote"
        logger.info(f"APIClient инициализирован в режиме: {mode}")

    async def register_user(self, telegram_id: int, username: str) -> Optional[Dict[str, Any]]:
        if self.mode == "local": # Используется пока локальная БД
            user = get_user_by_telegram_id(telegram_id)
            if user:
                return user
            return db_register_user(telegram_id, username, username)
        else:
            logger.warning("Remote mode not implemented yet")
            return None

    async def check_user_access(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        if self.mode == "local":
            return get_user_by_telegram_id(telegram_id)
        else:
            return None

    async def create_project(self, telegram_id: int, text: str, title: str = "Без названия"):
        if self.mode == "local":
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                return None

            # создание проекта в БД
            return db_create_project(
                user_id=user['id'],
                text=text,
                title=title,
                content_type=content_type,
                model=model
            )
        else:
            # TODO: Реализовать HTTP-запрос к реальному API
            logger.warning("Удаленный режим еще не реализован")
            return None

    async def get_projects(self, telegram_id: int, limit: int = 10):
        if self.mode == "local":
            return get_user_projects(telegram_id, limit)
        else:
            return []

    async def get_favorites(self, telegram_id: int):
        if self.mode == "local":
            return get_user_favorites(telegram_id)
        else:
            return []
# Проверrf, в избранном ли проект
    async def is_favorite(self, telegram_id: int, project_id: int) -> bool:

        if self.mode == "local":
            from database import get_user_favorites
            favorites = get_user_favorites(telegram_id)
            return any(p['id'] == project_id for p in favorites)
        return False

    # Админ-функции
    async def get_pending_users_list(self):
        # Список пользователей на одобрение
        if self.mode == "local":
            return get_pending_users()
        return []

    async def approve_user_by_id(self, telegram_id: int) -> bool:
        # Одобрить пользователя
        if self.mode == "local":
            return approve_user(telegram_id)
        return False


# Для переключения режима: "local" для разработки, "remote" для продакшена
api_client = APIClient(mode="local")