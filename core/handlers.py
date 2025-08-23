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

# === Start / Menu Utama ===
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>🤖 OpenWrt TeleMonitor</b>\n<i>Developer: @nodexservice</i>\n\n"
        "Bot ini membantu memantau perangkat WLAN & modem di STB OpenWrt.\n\n"
        "Pilih menu utama:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 WLAN", callback_data="menu_wlan")],
        [InlineKeyboardButton("🌐 MODEM", callback_data="menu_modem")]
    ])
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=keyboard)

# === Menu WLAN / MODEM ===
async def menu_wlan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    msg = "<b>📡 Menu WLAN</b>\n<i>Pantau & kelola perangkat WiFi STB</i>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Daftar Perangkat", callback_data="daftar_perangkat_menu")],
        [InlineKeyboardButton("📊 Statistik", callback_data="stats")],
        [InlineKeyboardButton("⏳ Uptime", callback_data="uptime")],
        [InlineKeyboardButton("⚙️ Toggle Auto-Scan", callback_data="toggle_scan")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="main_menu")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

async def menu_modem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    msg = "<b>🌐 Menu MODEM</b>\n<i>Lihat status & info modem</i>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ℹ️ Info Modem", callback_data="info_modem")],
        [InlineKeyboardButton("🔄 Toggle Refresh IP", callback_data="toggle_refreship")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="main_menu")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

# === Menu Daftar Perangkat ===
async def daftar_perangkat_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    msg = "<b>📋 Menu Daftar Perangkat</b>\n<i>Pilih kategori daftar:</i>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 Aktif", callback_data="list_active")],
        [InlineKeyboardButton("📂 Terdaftar", callback_data="list_registered")],
        [InlineKeyboardButton("🆕 Belum Terdaftar", callback_data="list_unregistered")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_wlan")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

# === List Aktif ===
async def list_active(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    devices, info = get_connected_devices()
    if not devices:
        await q.edit_message_text("<b>📡 Tidak ada perangkat aktif</b>", parse_mode="HTML")
        return
    msg = "<b>📡 Perangkat Aktif</b>\n"
    for mac in devices:
        dname = get_device_name(mac)
        ip = info.get(mac, {}).get("ip", "-")
        host = info.get(mac, {}).get("hostname", "TIDAK DIKETAHUI")
        msg += f"\n• <b>{dname}</b>\n  MAC: {fmt(mac)} | IP: {fmt(ip)} | Host: {fmt(host)}"
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")]
    ]))

# === List Terdaftar ===
async def list_registered(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if not DEVICES:
        await q.edit_message_text("<b>📂 Tidak ada perangkat terdaftar</b>", parse_mode="HTML")
        return
    msg = "<b>📂 Perangkat Terdaftar</b>\n"
    for mac, data in DEVICES.items():
        msg += (
            f"\n• <b>{data['name']}</b>\n"
            f"  MAC: {fmt(mac)} | Last seen: {fmt(data.get('last_seen','-'))} | IP: {fmt(data.get('last_ip','-'))}\n"
            f"  Blacklist: {fmt('Ya' if data.get('blacklist') else 'Tidak')}"
        )
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")]
    ]))

# === List Belum Terdaftar ===
async def list_unregistered(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    devices, info = get_connected_devices()
    unregistered = [mac for mac in devices if mac not in DEVICES]
    if not unregistered:
        await q.edit_message_text("<b>🆕 Tidak ada perangkat belum terdaftar</b>", parse_mode="HTML")
        return
    msg = "<b>🆕 Perangkat Belum Terdaftar</b>\nPilih salah satu untuk detail:"
    keyboard = []
    for mac in unregistered:
        label = info.get(mac, {}).get("hostname", mac)
        keyboard.append([InlineKeyboardButton(label, callback_data=f"regdetail:{mac}")])
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="daftar_perangkat_menu")])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# === Register Detail / Add ===
async def reg_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mac = q.data.split(":")[1]
    devices, info = get_connected_devices()
    host = info.get(mac, {}).get("hostname", "TIDAK DIKETAHUI")
    ip = info.get(mac, {}).get("ip", "-")
    msg = (
        "<b>📋 Detail Device</b>\n"
        f"• MAC: {fmt(mac)}\n"
        f"• Host: {fmt(host)}\n"
        f"• IP: {fmt(ip)}\n"
        "• Status: Belum Terdaftar"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tambahkan", callback_data=f"regadd:{mac}")],
        [InlineKeyboardButton("❌ Batal", callback_data="list_unregistered")]
    ])
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=keyboard)

async def reg_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mac = q.data.split(":")[1]
    pending_register[q.from_user.id] = mac
    await q.edit_message_text(f"✏️ Kirim nama untuk device {fmt(mac)}", parse_mode="HTML")

# === Text Input (Register / Rename) ===
async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id in pending_register:
        mac = pending_register.pop(user_id)
        DEVICES[mac] = {"name": text, "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "last_ip": "-", "blacklist": False}
        save_devices(DEVICES)
        await update.message.reply_text(f"✅ Device {fmt(mac)} berhasil didaftarkan dengan nama <b>{text}</b>", parse_mode="HTML")

    elif user_id in pending_rename:
        mac = pending_rename.pop(user_id)
        if mac in DEVICES:
            DEVICES[mac]["name"] = text
            save_devices(DEVICES)
            await update.message.reply_text(f"✏️ Device {fmt(mac)} berhasil diganti nama menjadi <b>{text}</b>", parse_mode="HTML")

# === Blacklist / Rename Button ===
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

# === Statistik & Uptime ===
async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
    await send_all(ctx.application, loops.CHAT_IDS, msg)

async def uptime(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        out = subprocess.check_output(["uptime", "-p"], text=True).strip()
    except Exception:
        out = "Unknown"
    msg = f"<b>⏳ STB Uptime</b>\nDurasi: {fmt(out)}"
    await send_all(ctx.application, loops.CHAT_IDS, msg)

async def toggle_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    loops.auto_scan = not loops.auto_scan
    status = "Aktif ✅" if loops.auto_scan else "Nonaktif ❌"
    await send_all(ctx.application, loops.CHAT_IDS, f"⚙️ Auto-scan diubah ke: <b>{status}</b>")

# === Info Modem ===
async def info_modem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    modems = get_all_modems()
    if not modems:
        msg = "❌ <b>Tidak ada modem terdeteksi</b>"
    else:
        msg = "<b>🌐 Info Modem</b>\n"
        for m in modems:
            dev = m.get("device","-")
            ip = m["ipv4-address"][0]["address"] if "ipv4-address" in m else "-"
            uptime = m.get("uptime","-")
            stats = get_device_stats(dev)
            rx = stats.get("statistics", {}).get("rx_bytes", "-")
            tx = stats.get("statistics", {}).get("tx_bytes", "-")
            msg += (
                f"\n<b>Interface:</b> {fmt(m['interface'])}\n"
                f"• Device: {fmt(dev)}\n"
                f"• IP: {fmt(ip)}\n"
                f"• Uptime: {fmt(uptime)}\n"
                f"• RX: {fmt(rx)} bytes\n"
                f"• TX: {fmt(tx)} bytes\n"
            )
        ports = list_serial_ports()
        if ports:
            msg += "\n<b>📡 Serial Port:</b>\n" + "\n".join(f"• {fmt(p)}" for p in ports)
    await send_all(ctx.application, loops.CHAT_IDS, msg)

# === Register Semua Handler ===
def register(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_wlan, pattern="^menu_wlan$"))
    app.add_handler(CallbackQueryHandler(menu_modem, pattern="^menu_modem$"))
    app.add_handler(CallbackQueryHandler(daftar_perangkat_menu, pattern="^daftar_perangkat_menu$"))
    app.add_handler(CallbackQueryHandler(list_active, pattern="^list_active$"))
    app.add_handler(CallbackQueryHandler(list_registered, pattern="^list_registered$"))
    app.add_handler(CallbackQueryHandler(list_unregistered, pattern="^list_unregistered$"))
    app.add_handler(CallbackQueryHandler(reg_detail, pattern="^regdetail:"))
    app.add_handler(CallbackQueryHandler(reg_add, pattern="^regadd:"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(rename:|blacklist:)"))
    app.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(uptime, pattern="^uptime$"))
    app.add_handler(CallbackQueryHandler(toggle_scan, pattern="^toggle_scan$"))
    app.add_handler(CallbackQueryHandler(info_modem, pattern="^info_modem$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
