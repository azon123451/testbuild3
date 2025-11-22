#!/usr/bin/env python3
"""
Web server with integrated Telegram bot for Scalingo
"""
import os
import json
import asyncio
import threading
from pathlib import Path
from flask import Flask, send_from_directory, jsonify

# Import bot functionality
from bot.main import main as bot_main, configure_logging, is_bot_configured

# Create Flask app
app = Flask(__name__, static_folder=None)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
WEBAPP_DIR = PROJECT_ROOT / "webapp"
CATALOG_JSON_PATH = WEBAPP_DIR / "catalog.json"

bot_thread: threading.Thread | None = None

def run_bot():
    """Run Telegram bot in background thread"""
    try:
        # Check if bot can be configured
        if not is_bot_configured():
            print("Bot not configured (TELEGRAM_BOT_TOKEN not set), skipping bot startup")
            return

        print("Starting Telegram bot...")
        # Configure logging for bot
        configure_logging()
        # Run bot in asyncio event loop
        asyncio.run(bot_main())
    except Exception as e:
        print(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

def ensure_bot_thread() -> None:
    """Start bot thread if not already running"""
    global bot_thread
    if bot_thread and bot_thread.is_alive():
        return
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

@app.route('/')
def index():
    """Serve the main webapp page"""
    return send_from_directory(WEBAPP_DIR, 'index.html')

@app.route('/catalog.json')
def catalog():
    """Serve the catalog JSON file with no-cache headers"""
    response = send_from_directory(WEBAPP_DIR, 'catalog.json')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/health')
def health():
    """Health check endpoint for Scalingo"""
    bot_status = "configured" if is_bot_configured() else "not_configured"
    return jsonify({
        "status": "ok",
        "service": "telegram-bot-webapp",
        "bot_status": bot_status
    })

# WSGI application for gunicorn
application = app

# Start bot thread as soon as module is imported (works both locally and under Gunicorn)
ensure_bot_thread()

if __name__ == '__main__':
    # Run web server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)