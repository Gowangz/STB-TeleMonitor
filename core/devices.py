import os, subprocess, logging, json
from datetime import datetime
from .utils import save_devices

DEVICES_FILE = "devices.json"
try:
    with open(DEVICES_FILE) as f:
        DEVICES = json.load(f)
except:
    DEVICES = {}

def get_connected_devices():
    devices = set()
    info = {}
    try:
        if os.path.exists("/tmp/dhcp.leases"):
            with open("/tmp/dhcp.leases") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        mac = parts[1].upper()
                        ip = parts[2]
                        hostname = parts[3] if parts[3] != "*" else "TIDAK DIKETAHUI"
                        devices.add(mac)
                        info[mac] = {"hostname": hostname, "ip": ip}
        try:
            iw_out = subprocess.check_output(["iw", "dev", "wlan0", "station", "dump"], text=True)
            for l in iw_out.splitlines():
                if "Station" in l:
                    mac = l.split()[1].upper()
                    devices.add(mac)
                    if mac not in info:
                        info[mac] = {"hostname": "TIDAK DIKETAHUI", "ip": "-"}
        except Exception:
            pass
    except Exception as e:
        logging.error("Error reading devices: %s", e)
    return devices, info

def update_last_seen(devices_dict, mac, name=None, ip="-"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if mac not in devices_dict:
        devices_dict[mac] = {"name": name if name else mac, "last_seen": now, "last_ip": ip, "blacklist": False}
    else:
        devices_dict[mac]["last_seen"] = now
        devices_dict[mac]["last_ip"] = ip
        if name:
            devices_dict[mac]["name"] = name
    save_devices(devices_dict)

def get_device_name(mac):
    return DEVICES.get(mac, {}).get("name", mac)
