from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Final, List, Mapping, Sequence

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN: Final = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8047115088:AAGnS5O4O5NzWz5c7BUgpI2LnkDq4XXbit4"
)
WEBAPP_URL: Final = os.environ.get(
    "WEBAPP_URL",
    "https://azon123451.github.io/testbuild4/",  # GitHub Pages с mini app
)
ADMIN_CHAT_ID_RAW = os.environ.get("ADMIN_CHAT_ID")
ADMIN_CHAT_ID: Final[int | None] = int(ADMIN_CHAT_ID_RAW) if ADMIN_CHAT_ID_RAW else None
CATALOG_FILE = Path(os.environ.get("CATALOG_FILE", "catalog.json"))
BUTTON_TEXT: Final = "Открыть мини‑приложение"
WELCOME_MESSAGE: Final = (
    "Нажмите кнопку ниже, чтобы открыть мини‑приложение. "
    "Если не открывается, обновите Telegram."
)

keyboard_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(BUTTON_TEXT, web_app=WebAppInfo(url=WEBAPP_URL))]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Открой мини‑приложение 👇",
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


def _format_cart_items(cart: Sequence[Mapping[str, object]]) -> str:
    lines: List[str] = []
    for item in cart:
        name = str(item.get("name", "Товар"))
        variant = item.get("variant")
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        suffix = f" ({variant})" if variant else ""
        lines.append(f"• {name}{suffix} — {qty} шт. × {price} ₽")
    return "\n".join(lines) if lines else "Корзина пуста"


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получает данные из WebApp (оформленные заказы/изменения каталога)."""
    message = update.effective_message
    if not message or not message.web_app_data:
        return

    raw_data = message.web_app_data.data
    try:
        payload = json.loads(raw_data)
    except json.JSONDecodeError:
        await message.reply_text("Не удалось распознать данные мини‑приложения 😔")
        logger.warning("Invalid WebApp payload: %s", raw_data)
        return

    action = payload.get("action")
    if action == "order":
        await _handle_order(payload, update, context)
    elif action == "catalog_update":
        await _handle_catalog_update(payload, update)
    else:
        await message.reply_text("Мини‑приложение прислало неизвестное действие.")
        logger.info("Unknown WebApp action: %s", payload)


async def _handle_order(
    payload: Mapping[str, object],
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    cart = payload.get("cart")
    total = payload.get("total")
    name = payload.get("name")
    phone = payload.get("phone")
    address = payload.get("address")
    payment = payload.get("payment")
    delivery = payload.get("delivery")

    text_lines = [
        "<b>🛒 Новый заказ</b>",
        f"Имя: {name}",
        f"Телефон: {phone}",
        f"Доставка: {delivery}",
        f"Адрес: {address}",
        f"Оплата: {payment}",
        "",
        _format_cart_items(cart if isinstance(cart, list) else []),
        "",
        f"<b>Итого: {total} ₽</b>",
    ]
    summary = "\n".join(text_lines)

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=summary,
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Не удалось отправить заказ админу: %s", exc)

    await update.effective_message.reply_text(
        "Спасибо! Заказ получили и скоро свяжемся.",
        reply_markup=keyboard_markup,
    )


async def _handle_catalog_update(
    payload: Mapping[str, object],
    update: Update,
) -> None:
    catalog = payload.get("catalog")
    if not isinstance(catalog, Mapping):
        await update.effective_message.reply_text("Каталог не распознан.")
        return

    try:
        CATALOG_FILE.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("Ошибка сохранения каталога: %s", exc)
        await update.effective_message.reply_text("Не удалось сохранить каталог.")
        return

    await update.effective_message.reply_text(
        f"Каталог обновлён и сохранён в {CATALOG_FILE}",
        reply_markup=keyboard_markup,
    )


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
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data)
    )
    logger.info("Бот запущен. Ожидаем события...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

