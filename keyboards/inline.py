from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# главное меню бота
def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Новый проект"), KeyboardButton(text="⏳ Прогресс")],
            [KeyboardButton(text="📁 История"), KeyboardButton(text="⭐ Избранное")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_content_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=" Изображение", callback_data="content_type_image"),
            InlineKeyboardButton(text="🎬 Видео", callback_data="content_type_video")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")
        ]
    ])
    return keyboard


def get_model_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=" ComfyUI (Stable Diffusion)", callback_data="model_comfyui")
        ],
        [
            InlineKeyboardButton(text="🤖 Qwen AI", callback_data="model_qwen")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")
        ]
    ])
    return keyboard


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
    ])
    return keyboard