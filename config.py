import os
import logging
from dotenv import load_dotenv

# Загруска в ОС переменных
load_dotenv()

# Настройка логов
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class Config:

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    
    ADMIN_ID = os.getenv("ADMIN_ID")
    if ADMIN_ID:
        try:
            ADMIN_ID = int(ADMIN_ID)
        except ValueError:
            logger.warning(f"Неверный формат ADMIN_ID: {ADMIN_ID}")
            ADMIN_ID = None

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

config = Config()