# Telegram бот с кнопкой «Старт»

## Запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Укажите токен Telegram-бота и адрес мини‑приложения:
   ```bash
   $env:TELEGRAM_BOT_TOKEN="ваш_токен"      # PowerShell
   export TELEGRAM_BOT_TOKEN="ваш_токен"    # bash/zsh

   $env:WEBAPP_URL="https://ваш-домен/webapp/index.html"
   export WEBAPP_URL="https://ваш-домен/webapp/index.html"

   # необязательно: куда отправлять заказы и куда сохранять каталог
   $env:ADMIN_CHAT_ID="123456789"
   $env:CATALOG_FILE="catalog.json"
   ```
3. Запустите скрипт:
   ```bash
   python main.py
   ```

После запуска у пользователя появится клавиатура с кнопкой «Открыть мини‑приложение».
По нажатию Telegram откроет WebApp по адресу `WEBAPP_URL` (файл `index.html` из
корня проекта нужно выложить на HTTPS‑хостинг — GitHub Pages, Vercel, Netlify,
любой CDN или Telegram Mini App hosting).

## Как работает mini app

- `index.html` использует Telegram WebApp SDK (`telegram-web-app.js`), показывает
  каталог и корзину, а при оформлении заказа отправляет данные в бота через
  `tg.sendData`. Стартовый каталог хранится в `catalog.json`; его можно
  отредактировать и задеплоить вместе со страницей. Админ-панель внутри mini app
  умеет выгружать/загружать JSON и отправлять изменения в бота.
- Бот принимает эти события (тип `web_app_data`). Для `action=order` он
  формирует текст с заказом, благодарит пользователя и, если задан
  `ADMIN_CHAT_ID`, дублирует заказ в указанный чат.
- Для `action=catalog_update` бот сохраняет присланный JSON в файл
  `CATALOG_FILE` (по умолчанию `catalog.json`). Далее этот файл можно повторно
  задеплоить на фронтенд-хостинг, чтобы mini app увидел свежие данные.

Таким образом, достаточно задеплоить `index.html` + `catalog.json` на HTTPS,
задать `WEBAPP_URL`, и кнопка в Telegram-боте будет открывать адаптированное
mini app с оформлением заказов.

