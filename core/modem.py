import subprocess, json, logging

def get_all_modems():
    try:
        dump = subprocess.check_output(["ubus", "call", "network.interface", "dump"], text=True)
        data = json.loads(dump)
        all_ifaces = {i['interface']: i for i in data['interface']}

        fw = subprocess.check_output("uci show firewall | grep network", shell=True, text=True)
        wan_ifaces = []
        for line in fw.splitlines():
            if ".network=" in line and "wan" in line:
                nets = line.split("=")[1].strip("'").split()
                wan_ifaces.extend(nets)

        modems = {name: all_ifaces[name] for name in wan_ifaces if name in all_ifaces}
        return modems
    except Exception as e:
        logging.error("Error get_all_modems: %s", e)
    return {}

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
