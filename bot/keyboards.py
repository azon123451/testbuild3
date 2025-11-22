from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


def build_start_keyboard() -> ReplyKeyboardMarkup:
	"""
	Create a persistent reply keyboard with a 'СТАРТ' button.
	The keyboard sits at the bottom of the chat.
	"""
	button = KeyboardButton(text="СТАРТ")
	return ReplyKeyboardMarkup(
		keyboard=[[button]],
		resize_keyboard=True,
		one_time_keyboard=False,
		is_persistent=True,
	)


def build_open_app_keyboard(mini_app_url: str | None, manager_username: str | None) -> InlineKeyboardMarkup:
	"""
	Build inline keyboard with buttons:
	- 'Открыть приложение' (Mini App / WebApp) - if URL provided
	- 'Связь с оператором' (opens chat with manager) - if username provided
	- At least one button is guaranteed to be present
	"""
	buttons: list[list[InlineKeyboardButton]] = []

	if mini_app_url:
		buttons.append([
			InlineKeyboardButton(
				text="Открыть приложение",
				web_app=WebAppInfo(url=mini_app_url),
			)
		])

	if manager_username:
		link = f"https://t.me/{manager_username.lstrip('@')}"
		buttons.append([
			InlineKeyboardButton(
				text="Связь с оператором",
				url=link,
			)
		])

	# Fallback: if no buttons added, add a help button
	if not buttons:
		buttons.append([
			InlineKeyboardButton(
				text="Связь с поддержкой",
				url="https://t.me/neft_shop_manager86",  # fallback manager
			)
		])

	return InlineKeyboardMarkup(inline_keyboard=buttons)


