# Telegram бот с кнопкой «Старт»

## Запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Укажите токен Telegram-бота:
   ```bash
   $env:TELEGRAM_BOT_TOKEN="ваш_токен"      # PowerShell
   export TELEGRAM_BOT_TOKEN="ваш_токен"    # bash/zsh
   ```
3. Запустите скрипт:
   ```bash
   python bot.py
   ```

После запуска у пользователя появится клавиатура с единственной кнопкой «Старт».
Каждое нажатие отправляет приветственное сообщение в чат.

