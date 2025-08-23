#!/bin/sh
# Installer OpenWrt TeleMonitor (versi modular final)
# Developer: @nodexservice

echo "🚀 Instalasi OpenWrt TeleMonitor"

# === 1. Install dependency ===
echo "👉 Menginstall dependency..."
opkg update
opkg install python3 python3-pip git-core ca-certificates

# === 2. Install python-telegram-bot ===
pip3 install --upgrade pip
pip3 install python-telegram-bot --break-system-packages

# === 3. Input interaktif ===
echo "👉 Masukkan BOT TOKEN:"
read BOT_TOKEN
echo "👉 Masukkan CHAT ID admin (pisahkan dengan koma jika lebih dari satu):"
read CHAT_IDS
echo "👉 Interval scan dalam detik [15]:"
read SCAN_INTERVAL
[ -z "$SCAN_INTERVAL" ] && SCAN_INTERVAL=15

# Format chat_ids ke JSON array
CHAT_IDS_JSON=$(echo "$CHAT_IDS" | sed 's/,/","/g')
CHAT_IDS_JSON="[$(echo "\"$CHAT_IDS_JSON\"")]"

# === 4. Generate config.json ===
cat > config.json <<EOF
{
  "bot_token": "$BOT_TOKEN",
  "chat_ids": $CHAT_IDS_JSON,
  "scan_interval": $SCAN_INTERVAL
}
EOF

# === 5. Buat devices.json kosong ===
if [ ! -f devices.json ]; then
  echo "{}" > devices.json
fi

# === 6. Buat folder backup ===
mkdir -p backup

# === 7. Buat init script untuk bot ===
INIT_FILE="/etc/init.d/telemon"
cat > $INIT_FILE <<'EOL'
#!/bin/sh /etc/rc.common
# Init script OpenWrt TeleMonitor
START=99
STOP=10

USE_PROCD=1
PROG="/usr/bin/python3"
ARGS="/root/STB-TeleMonitor/bot.py"

start_service() {
    procd_open_instance
    procd_set_param command $PROG $ARGS
    procd_set_param respawn
    procd_close_instance
}
EOL
chmod +x $INIT_FILE

# === 8. Enable service ===
/etc/init.d/telemon enable

echo "✅ Instalasi selesai!"
echo "👉 Jalankan manual dengan: python3 bot.py"
echo "👉 Atau start service: /etc/init.d/telemon start"
