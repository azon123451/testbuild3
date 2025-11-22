"""
Простой Telegram-бот с клавиатурой из одной кнопки «Старт».

После нажатия выводится приветственное сообщение в чате.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Final

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN: Final = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8047115088:AAGnS5O4O5NzWz5c7BUgpI2LnkDq4XXbit4"
)
BUTTON_TEXT: Final = "Старт"
WELCOME_MESSAGE: Final = (
    "Привет! 👋\n"
    "Я готов помочь. Нажми кнопку «Старт», чтобы увидеть это сообщение снова."
)

keyboard_markup = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(BUTTON_TEXT)]],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Нажми «Старт» 👇",
)


async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственный текст и клавиатуру."""
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=WELCOME_MESSAGE,
            reply_markup=keyboard_markup,
        )
        logger.info("Приветственное сообщение отправлено в чат %s", update.effective_chat.id)


async def on_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Хэндлер команды /start."""
    await send_welcome(update, context)


async def on_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Реагирует на текст от кнопки «Старт» (кнопка отправляет обычное сообщение)."""
    await send_welcome(update, context)


def main() -> None:
    token = BOT_TOKEN
    if not token:
        raise RuntimeError(
            "Укажите токен бота: задайте переменную окружения TELEGRAM_BOT_TOKEN "
            "или пропишите токен напрямую в BOT_TOKEN."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", on_command_start))
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.Regex(re.compile(fr"^{BUTTON_TEXT}$", flags=re.IGNORECASE)),
            on_button_press,
        )
    )

    logger.info("Бот запущен. Ожидаем события...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

