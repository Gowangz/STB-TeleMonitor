#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, logging, json
from telegram.ext import Application
from core import handlers, loops

CONFIG_FILE = "config.json"
with open(CONFIG_FILE) as f:
    CONFIG = json.load(f)

BOT_TOKEN = CONFIG["bot_token"]
loops.CHAT_IDS = CONFIG["chat_ids"]
loops.SCAN_INTERVAL = CONFIG.get("scan_interval", 15)

def main():
    logging.basicConfig(
        filename="bot.log",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("").addHandler(logging.StreamHandler())

    app = Application.builder().token(BOT_TOKEN).build()
    handlers.register(app)

    asyncio.get_event_loop().create_task(loops.auto_scan_loop(app))
    asyncio.get_event_loop().create_task(loops.refresh_ip_loop(app))

    logging.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
