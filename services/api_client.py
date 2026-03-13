import aiohttp
import logging
from typing import Optional, Dict, Any
from config import config

logger = logging.getLogger(__name__)

class APIClient:

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        # создание сессии
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def register_user(self, telegram_id: int, username: str) -> Optional[Dict[str, Any]]:
        """
        Регистрирует или находит пользователя в БД.

        Args:
            telegram_id: Telegram ID пользователя
            username: Username пользователя (@name)

        Returns:
            Данные пользователя или None при ошибке
        """
        try:
            session = await self._get_session()
            async with session.post(
                    f"{self.base_url}/api/users/register",
                    json={
                        "telegram_id": telegram_id,
                        "username": username
                    }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ошибка регистрации пользователя: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Исключение при регистрации пользователя: {e}")
            return None

    async def check_user_access(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Проверяет, есть ли у пользователя доступ.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Данные пользователя с полем is_approved или None
        """
        try:
            session = await self._get_session()
            async with session.get(
                    f"{self.base_url}/api/users/{telegram_id}/check"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    # Пользователь не найден — нужно зарегистрировать
                    return None
                else:
                    logger.error(f"Ошибка проверки доступа: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Исключение при проверке доступа: {e}")
            return None


api_client = APIClient(base_url=config.API_URL, timeout=config.API_TIMEOUT)