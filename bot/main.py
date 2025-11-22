import asyncio
import logging
import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Set

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message, BotCommand
from dotenv import load_dotenv

from .keyboards import build_start_keyboard, build_open_app_keyboard


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
WELCOME_IMAGE_PATH = ASSETS_DIR / "neft.jpg"
WEBAPP_DIR = PROJECT_ROOT / "webapp"
CATALOG_JSON_PATH = WEBAPP_DIR / "catalog.json"


@dataclass
class Config:
	token: str
	mini_app_url: str | None
	manager_username: str | None
	admin_user_ids: Set[int]


def is_bot_configured() -> bool:
	"""Check if bot can be configured"""
	load_dotenv()
	bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
	return bool(bot_token)

def load_config_from_env() -> Config:
	"""
	Load bot token from .env or environment.
	Raises a clear error if missing.
	"""
	load_dotenv()
	bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
	if not bot_token:
		raise RuntimeError(
			"TELEGRAM_BOT_TOKEN is not set. Create a .env file or set the env var."
		)
	mini_app_url = os.getenv("MINI_APP_URL", "").strip() or None
	manager_username = os.getenv("MANAGER_USERNAME", "").strip() or None
	raw_admins = os.getenv("ADMIN_USER_IDS", "").strip()
	admin_ids: Set[int] = set()
	for part in raw_admins.split(","):
		part = part.strip()
		if not part:
			continue
		try:
			admin_ids.add(int(part))
		except ValueError:
			logging.getLogger(__name__).warning("Skip invalid ADMIN_USER_IDS entry: %r", part)
	return Config(
		token=bot_token,
		mini_app_url=mini_app_url,
		manager_username=manager_username,
		admin_user_ids=admin_ids,
	)


def configure_logging() -> None:
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s | %(levelname)8s | %(name)s | %(message)s",
	)


def build_dispatcher(config: Config) -> Dispatcher:
	dp = Dispatcher()

	@dp.message(CommandStart())
	async def handle_command_start(message: Message) -> None:
		keyboard = build_start_keyboard()

		if WELCOME_IMAGE_PATH.exists():
			photo = FSInputFile(WELCOME_IMAGE_PATH)
			await message.answer_photo(
				photo=photo,
				caption="НЕФТЬ",
				reply_markup=keyboard,
			)
		else:
			# Fallback if the image is not provided yet
			await message.answer(
				text="НЕФТЬ",
				reply_markup=keyboard,
			)

	@dp.message(F.text.casefold() == "старт")
	async def handle_start_flow(message: Message) -> None:
		welcome_text = (
			"Добро пожаловать👋\n\n"
			"Нажмите кнопку \"Открыть приложение\" чтобы просмотреть каталог\n\n"
			"🏪 Режим работы указан у менеджера\n\n"
			"🚛 Доставляем по всему городу"
		)
		inline_kb = build_open_app_keyboard(
			mini_app_url=config.mini_app_url,
			manager_username=config.manager_username or "neft_shop_manager86",
		)
		await message.answer(welcome_text, reply_markup=inline_kb)

	@dp.message(F.web_app_data)
	async def handle_webapp_order(message: Message) -> None:
		try:
			raw = message.web_app_data.data if message.web_app_data else None  # type: ignore[attr-defined]
			data = json.loads(raw or "{}")
			action = (data.get("action") or "").lower()
			if action == "catalog_update":
				user_id = message.from_user.id if message.from_user else 0
				if not config.admin_user_ids or user_id not in config.admin_user_ids:
					await message.answer("Недостаточно прав для обновления каталога.")
					return
				catalog = data.get("catalog")
				if not isinstance(catalog, dict):
					await message.answer("Некорректные данные каталога.")
					return
				WEBAPP_DIR.mkdir(parents=True, exist_ok=True)
				with CATALOG_JSON_PATH.open("w", encoding="utf-8") as f:
					json.dump(catalog, f, ensure_ascii=False, indent=2)
					f.write("\n")
				await message.answer("✅ catalog.json обновлён на сервере.")
				return

			# default: assume it's an order
			items = data.get("cart", [])
			total = data.get("total", 0)
			lines = []
			for i in items:
				name = i.get("name", "Товар")
				variant = i.get("variant") or "Стандарт"
				qty = int(i.get("qty", 1))
				price = int(i.get("price", 0))
				lines.append(f"- {name} ({variant}) × {qty} = {price * qty} ₽")
			summary = "\n".join(lines) if lines else "Пусто"
			text = (
				"✅ Заказ принят!\n\n"
				f"{summary}\n\n"
				f"Итого: {total} ₽\n"
				f"Имя: {data.get('name','—')}\n"
				f"Телефон: {data.get('phone','—')}\n"
				f"Адрес: {data.get('address','—')}\n"
				f"Оплата: {data.get('payment','—')}\n"
				f"Доставка: {data.get('delivery','—')}"
			)
			await message.answer(text)
		except Exception:
			await message.answer("Не удалось обработать заказ. Попробуйте ещё раз.")

	# Optional: reply to any other text to hint at /start
	@dp.message()
	async def handle_fallback(message: Message) -> None:
		if message.text:
			await message.answer("Нажмите /start, чтобы начать.")

	return dp


async def main() -> None:
	configure_logging()
	config = load_config_from_env()

	logging.getLogger(__name__).info("Initializing Telegram bot...")

	bot = Bot(token=config.token, parse_mode=ParseMode.HTML)
	dp = build_dispatcher(config)

	# Set basic commands (shows in Telegram UI)
	await bot.set_my_commands([
		BotCommand(command="start", description="Запуск бота"),
	])

	logging.getLogger(__name__).info("Bot initialized successfully, starting polling...")
	await dp.start_polling(bot)


if __name__ == "__main__":
	# On Windows, default event loop is fine; on Unix, uvloop is used via requirements
	try:
		asyncio.run(main())
	except (KeyboardInterrupt, SystemExit):
		pass


