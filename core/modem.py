import subprocess, json, logging

def get_all_modems():
    try:
        data = subprocess.check_output(["ubus", "call", "network.interface", "dump"], text=True)
        info = json.loads(data)
        candidates = []
        for iface in info.get("interface", []):
            if iface.get("up") and "ipv4-address" in iface and iface["ipv4-address"]:
                candidates.append(iface)
        return candidates
    except Exception as e:
        logging.error("Error get_all_modems: %s", e)
    return []

def get_device_stats(dev_name):
    try:
        data = subprocess.check_output(
            ["ubus", "call", "network.device", "status", f'{{"name":"{dev_name}"}}'],
            text=True
        )
        return json.loads(data)
    except:
        return {}

def list_serial_ports():
    try:
        out = subprocess.check_output("ls -1 /dev/ttyUSB* /dev/ttyACM* 2>/dev/null", shell=True, text=True)
        return out.strip().splitlines()
    except Exception:
        return []
