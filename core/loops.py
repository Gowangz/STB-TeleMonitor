import asyncio
from datetime import datetime
from .devices import get_connected_devices, update_last_seen, get_device_name, DEVICES
from .utils import send_all, fmt

connected_devices = set()
auto_scan = False
notify_refresh_ip = False
old_ip = None
SCAN_INTERVAL = 15
CHAT_IDS = []

async def auto_scan_loop(app):
    global connected_devices
    while True:
        if auto_scan:
            curr, info = get_connected_devices()
            new = curr - connected_devices
            left = connected_devices - curr

            for mac in new:
                ip = info.get(mac, {}).get("ip", "-")
                host = info.get(mac, {}).get("hostname", "TIDAK DIKETAHUI")
                update_last_seen(DEVICES, mac, ip=ip)
                if DEVICES.get(mac, {}).get("blacklist"):
                    await send_all(app, CHAT_IDS, f"🚨 BLACKLIST CONNECTED: {fmt(mac)} | IP: {fmt(ip)}")
                else:
                    await send_all(app, CHAT_IDS,
                        f"📶 Device Connected\nName: {fmt(get_device_name(mac))}\nMAC: {fmt(mac)}\nHost: {fmt(host)}\nIP: {fmt(ip)}"
                    )

            for mac in left:
                last_ip = DEVICES.get(mac, {}).get("last_ip", "-")
                update_last_seen(DEVICES, mac, ip=last_ip)
                await send_all(app, CHAT_IDS,
                    f"❌ Device Disconnected\nName: {fmt(get_device_name(mac))}\nMAC: {fmt(mac)}\nIP: {fmt(last_ip)}\nLast seen: {fmt(DEVICES[mac]['last_seen'])}"
                )

            connected_devices = curr
        await asyncio.sleep(SCAN_INTERVAL)

async def refresh_ip_loop(app):
    global old_ip, notify_refresh_ip
    while True:
        if notify_refresh_ip:
            # TODO: implement refresh ip notif pakai get_all_modems()
            pass
        await asyncio.sleep(30)
