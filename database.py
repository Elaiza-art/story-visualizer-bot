import sqlite3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

DB_NAME = "bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Чтобы получать результаты как словари
    return conn

# Создание таблиц
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            is_approved BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_visit TIMESTAMP
        )
    """)

    # Таблица проектов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            text TEXT,
            content_type TEXT DEFAULT 'video',  
            model TEXT DEFAULT 'comfyui',       
            video_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Таблица избранного
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, project_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


init_db()


# Функционал для работы с пользователями

def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Находит пользователя по Telegram ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def register_user(telegram_id: int, username: str, full_name: str) -> Dict[str, Any]:
    """Регистрирует нового пользователя или возвращает существующего"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    existing = cursor.fetchone()

    if existing:
        # Обновляем last_visit
        cursor.execute(
            "UPDATE users SET last_visit = ? WHERE telegram_id = ?",
            (datetime.now(), telegram_id)
        )
        conn.commit()
        conn.close()
        return dict(existing)

    # Создание нового пользователя
    cursor.execute(
        """INSERT INTO users (telegram_id, username, full_name, is_approved, is_admin)
           VALUES (?, ?, ?, ?, ?)""",
        (telegram_id, username, full_name, False, False)
    )
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    new_user = cursor.fetchone()
    conn.close()

    logger.info(f"Зарегистрирован новый пользователь: {telegram_id}")
    return dict(new_user) if new_user else None


def approve_user(telegram_id: int) -> bool:
    """Одобряет доступ пользователю (для админа)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET is_approved = TRUE WHERE telegram_id = ?",
        (telegram_id,)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def get_pending_users() -> List[Dict[str, Any]]:
    """Возвращает список пользователей, ожидающих одобрения"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE is_approved = FALSE ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_users() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Функционал для работы с проектами  пользователей
def create_project(user_id: int, text: str, title: str = "Без названия",
                   content_type: str = "video", model: str = "comfyui") -> Optional[Dict[str, Any]]:
    """Создаёт новый проект"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO projects (user_id, title, text, content_type, model, status)
           VALUES (?, ?, ?, ?, ?, 'pending')""",
        (user_id, title, text, content_type, model)
    )
    conn.commit()

    project_id = cursor.lastrowid
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()

    return dict(project) if project else None


def get_user_projects(telegram_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.* FROM projects p
        JOIN users u ON p.user_id = u.id
        WHERE u.telegram_id = ?
        ORDER BY p.created_at DESC
        LIMIT ?
    """, (telegram_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_project_status(project_id: int, status: str, video_path: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    if video_path:
        cursor.execute(
            """UPDATE projects SET status = ?, video_path = ?, completed_at = ? WHERE id = ?""",
            (status, video_path, datetime.now(), project_id)
        )
    else:
        cursor.execute(
            """UPDATE projects SET status = ? WHERE id = ?""",
            (status, project_id)
        )
    conn.commit()
    conn.close()


# функционал для вкладки "Избранное"
def add_to_favorites(telegram_id: int, project_id: int) -> bool:
    """Добавляет проект в избранное"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Находим user_id по telegram_id
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False
        
        # Добавляем в избранное
        cursor.execute(
            "INSERT OR IGNORE INTO favorites (user_id, project_id) VALUES (?, ?)",
            (user['id'], project_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0
    except Exception as e:
        logging.error(f"Ошибка при добавлении в избранное: {e}")
        return False



def get_user_favorites(telegram_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.* FROM projects p
        JOIN favorites f ON p.id = f.project_id
        JOIN users u ON f.user_id = u.id
        WHERE u.telegram_id = ?
        ORDER BY f.added_at DESC
    """, (telegram_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Находим и удаляем проект из избранного"""
def remove_from_favorites(telegram_id: int, project_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False

        cursor.execute(
            "DELETE FROM favorites WHERE user_id = ? AND project_id = ?",
            (user['id'], project_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0
    except Exception as e:
        logging.error(f"Ошибка при удалении из избранного: {e}")
        return False