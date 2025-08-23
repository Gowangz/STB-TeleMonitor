from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import subprocess

from .devices import get_connected_devices, get_device_name, DEVICES
from .utils import fmt, send_all, save_devices
from .modem import get_all_modems, get_device_stats, list_serial_ports
from . import loops

pending_register = {}
pending_rename = {}

# === Menu Utama ===
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>🤖 OpenWrt TeleMonitor</b>\n<i>Developer: @nodexservice</i>\n\n"
        "Bot ini memantau perangkat <b>WLAN</b> & <b>MODEM</b> pada STB OpenWrt.\n\n"
        "Pilih menu utama:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 WLAN", callback_data="menu_wlan")],
        [InlineKeyboardButton("🌐 MODEM", callback_data="menu_modem")]
    ])
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=keyboard)

async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    msg = "📌 <b>Menu Utama</b>\nSilakan pilih kategori monitoring:"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 WLAN", callback_data="menu_wlan")],
        [InlineKeyboardButton("🌐 MODEM", callback_data="menu_modem")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

# === Menu WLAN ===
async def menu_wlan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    msg = "<b>📡 Menu WLAN</b>\n<i>Pantau & kelola perangkat WiFi</i>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Daftar Perangkat", callback_data="daftar_perangkat_menu")],
        [InlineKeyboardButton("📊 Statistik", callback_data="stats")],
        [InlineKeyboardButton("⏳ Uptime", callback_data="uptime")],
        [InlineKeyboardButton("⚙️ Toggle Auto-Scan", callback_data="toggle_scan")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="main_menu")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

# === Menu MODEM ===
async def menu_modem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    msg = "<b>🌐 Menu MODEM</b>\n<i>Monitor status modem & koneksi internet</i>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ Info Modem", callback_data="info_modem")],
        [InlineKeyboardButton("🔄 Toggle Refresh IP", callback_data="toggle_refreship")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="main_menu")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

# === Menu Daftar Perangkat WLAN ===
async def daftar_perangkat_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    msg = "<b>📋 Menu Daftar Perangkat</b>\n<i>Pilih kategori daftar perangkat:</i>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 Aktif", callback_data="list_active")],
        [InlineKeyboardButton("📂 Terdaftar", callback_data="list_registered")],
        [InlineKeyboardButton("🆕 Belum Terdaftar", callback_data="list_unregistered")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_wlan")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

# === List Perangkat Aktif ===
async def list_active(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    devices, info = get_connected_devices()
    if not devices:
        await q.edit_message_text("<b>📡 Tidak ada perangkat aktif</b>", parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")]]))
        return
    msg = "<b>📡 Perangkat Aktif</b>\n<i>Daftar perangkat yang sedang terhubung:</i>"
    keyboard = []
    for mac in devices:
        host = info.get(mac, {}).get("hostname", None)
        label = host if host and host != "TIDAK DIKETAHUI" else "UNKNOWN"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"detail:{mac}")])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === List Perangkat Terdaftar ===
async def list_registered(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if not DEVICES:
        await q.edit_message_text("<b>📂 Tidak ada perangkat terdaftar</b>", parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")]]))
        return
    msg = "<b>📂 Perangkat Terdaftar</b>\n<i>Semua perangkat yang pernah diregistrasi:</i>"
    keyboard = []
    for mac, data in DEVICES.items():
        label = data.get("name")
        if not label or label.strip() == "":
            label = data.get("hostname", "UNKNOWN")
        keyboard.append([InlineKeyboardButton(label, callback_data=f"detail:{mac}")])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === List Belum Terdaftar ===
async def list_unregistered(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    devices, info = get_connected_devices()
    unregistered = [mac for mac in devices if mac not in DEVICES]
    if not unregistered:
        await q.edit_message_text("<b>🆕 Tidak ada perangkat belum terdaftar</b>", parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")]]))
        return
    msg = "<b>🆕 Perangkat Belum Terdaftar</b>\n<i>Pilih salah satu untuk detail:</i>"
    keyboard = []
    for mac in unregistered:
        host = info.get(mac, {}).get("hostname", None)
        label = host if host and host != "TIDAK DIKETAHUI" else "UNKNOWN"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"regdetail:{mac}")])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === Detail Device ===
async def detail_device(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mac = q.data.split(":")[1]
    d = DEVICES.get(mac)
    devices, info = get_connected_devices()
    ip = info.get(mac, {}).get("ip", d.get("last_ip", "-") if d else "-")
    host = info.get(mac, {}).get("hostname", "TIDAK DIKETAHUI")

    msg = "<b>📋 Detail Device</b>\n"
    msg += f"• Name: <b>{d['name'] if d else 'Belum Terdaftar'}</b>\n"
    msg += f"• MAC: {fmt(mac)}\n"
    msg += f"• IP: {fmt(ip)}\n"
    msg += f"• Host: {fmt(host)}\n"
    msg += f"• Last Seen: {fmt(d['last_seen'] if d else '-')}\n"
    msg += f"• Blacklist: {fmt('Ya' if d and d.get('blacklist') else 'Tidak')}"

    keyboard = []
    if not d:
        keyboard.append([InlineKeyboardButton("✅ Register", callback_data=f"regadd:{mac}")])
    else:
        keyboard.append([InlineKeyboardButton("✏️ Rename", callback_data=f"rename:{mac}")])
        keyboard.append([InlineKeyboardButton("🚫 Blacklist", callback_data=f"blacklist:{mac}")])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === Register Device ===
async def reg_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mac = q.data.split(":")[1]
    pending_register[q.from_user.id] = mac
    await q.edit_message_text(f"✏️ Kirim nama untuk device {fmt(mac)}", parse_mode="HTML")

# === Handle Text Input (Register/Rename) ===
async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id in pending_register:
        mac = pending_register.pop(user_id)
        DEVICES[mac] = {"name": text, "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "last_ip": "-", "blacklist": False}
        save_devices(DEVICES)
        await update.message.reply_text(f"✅ Device {fmt(mac)} didaftarkan sebagai <b>{text}</b>", parse_mode="HTML")

    elif user_id in pending_rename:
        mac = pending_rename.pop(user_id)
        if mac in DEVICES:
            DEVICES[mac]["name"] = text
            save_devices(DEVICES)
            await update.message.reply_text(f"✏️ Device {fmt(mac)} diganti nama menjadi <b>{text}</b>", parse_mode="HTML")

# === Rename / Blacklist Handler ===
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    data = q.data
    if data.startswith("rename:"):
        mac = data.split(":")[1]
        pending_rename[q.from_user.id] = mac
        await q.edit_message_text(f"✏️ Kirim nama baru untuk device {fmt(mac)}", parse_mode="HTML")
    elif data.startswith("blacklist:"):
        mac = data.split(":")[1]
        if mac in DEVICES:
            DEVICES[mac]["blacklist"] = True
            save_devices(DEVICES)
            await q.edit_message_text(f"🚫 Device {fmt(mac)} ditambahkan ke blacklist", parse_mode="HTML")

# === Statistik WLAN ===
async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    total = len(DEVICES)
    active, _ = get_connected_devices()
    active_count = len(active)
    bl_count = sum(1 for d in DEVICES.values() if d.get("blacklist"))
    msg = (
        "<b>📊 Statistik WLAN</b>\n"
        f"• Total Terdaftar: {fmt(total)}\n"
        f"• Aktif Sekarang: {fmt(active_count)}\n"
        f"• Blacklist: {fmt(bl_count)}"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_wlan")]]
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === Uptime ===
async def uptime(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    try:
        out = subprocess.check_output(["uptime", "-p"], text=True).strip()
    except Exception:
        out = "Unknown"
    msg = f"<b>⏳ STB Uptime</b>\nDurasi: {fmt(out)}"
    keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_wlan")]]
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === Toggle Auto-Scan ===
async def toggle_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    loops.auto_scan = not loops.auto_scan
    status = "Aktif ✅" if loops.auto_scan else "Nonaktif ❌"
    msg = f"⚙️ Auto-scan diubah ke: <b>{status}</b>"
    keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_wlan")]]
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === Info Modem ===
async def info_modem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    modems = get_all_modems()
    if not modems:
        msg = "❌ <b>Tidak ada modem terdeteksi</b>"
        keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_modem")]]
        await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    msg = "<b>🌐 Info Modem</b>\n"
    for name, m in modems.items():
        dev = m.get("l3_device","-")
        ip = m["ipv4-address"][0]["address"] if "ipv4-address" in m else "-"
        uptime = m.get("uptime","-")
        stats = get_device_stats(dev)
        rx = stats.get("statistics", {}).get("rx_bytes", "-")
        tx = stats.get("statistics", {}).get("tx_bytes", "-")

        msg += (
            f"\n<b>Interface:</b> {fmt(name)}\n"
            f"• Device: {fmt(dev)}\n"
            f"• IP: {fmt(ip)}\n"
            f"• Uptime: {fmt(uptime)}\n"
            f"• RX: {fmt(rx)} bytes\n"
            f"• TX: {fmt(tx)} bytes\n"
        )

    ports = list_serial_ports()
    if ports:
        msg += "\n<b>📡 Serial Port:</b>\n" + "\n".join(f"• {fmt(p)}" for p in ports)

    keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_modem")]]
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === Register Semua Handler ===
def register(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(menu_wlan, pattern="^menu_wlan$"))
    app.add_handler(CallbackQueryHandler(menu_modem, pattern="^menu_modem$"))
    app.add_handler(CallbackQueryHandler(daftar_perangkat_menu, pattern="^daftar_perangkat_menu$"))
    app.add_handler(CallbackQueryHandler(list_active, pattern="^list_active$"))
    app.add_handler(CallbackQueryHandler(list_registered, pattern="^list_registered$"))
    app.add_handler(CallbackQueryHandler(list_unregistered, pattern="^list_unregistered$"))
    app.add_handler(CallbackQueryHandler(detail_device, pattern="^detail:"))
    app.add_handler(CallbackQueryHandler(reg_add, pattern="^regadd:"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(rename:|blacklist:)"))
    app.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(uptime, pattern="^uptime$"))
    app.add_handler(CallbackQueryHandler(toggle_scan, pattern="^toggle_scan$"))
    app.add_handler(CallbackQueryHandler(info_modem, pattern="^info_modem$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
