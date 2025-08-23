import json, os, logging
from datetime import datetime

DEVICES_FILE = "devices.json"
BACKUP_DIR = "backup"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def fmt(text: str) -> str:
    return f"<code>{text}</code>"

def save_devices(devices):
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=2)
    backup_file = os.path.join(BACKUP_DIR, f"devices-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    with open(backup_file, "w") as bf:
        json.dump(devices, bf, indent=2)

async def send_all(app, chat_ids, text, **kwargs):
    for cid in chat_ids:
        try:
            await app.bot.send_message(chat_id=cid, text=text, parse_mode="HTML", **kwargs)
        except Exception as e:
            logging.error("Send error: %s", e)
