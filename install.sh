#!/bin/sh
# Installer & Upgrader OpenWrt TeleMonitor
# Developer: @nodexservice

BOT_DIR="/root/STB-TeleMonitor"
INIT_FILE="/etc/init.d/telemon"

echo "🚀 OpenWrt TeleMonitor Setup"

# === Menu Pilihan ===
if [ -d "$BOT_DIR" ]; then
    echo "📂 Bot sudah terdeteksi di $BOT_DIR"
    echo "Pilih opsi:"
    echo "1) Install Baru"
    echo "2) Upgrade (git pull, update lib, simpan config)"
    echo "3) Reinstall Bersih (hapus config & data)"
    read -p "👉 Pilihan [1-3]: " OPT
else
    OPT=1
fi

# === 1. Install Baru ===
if [ "$OPT" = "1" ]; then
    echo "👉 Install Baru..."
    opkg update
    opkg install python3 python3-pip git-core ca-certificates

    pip3 install --upgrade pip
    pip3 install python-telegram-bot --break-system-packages

    if [ ! -d "$BOT_DIR" ]; then
        git clone https://github.com/Gowangz/STB-TeleMonitor.git $BOT_DIR
    fi
    cd $BOT_DIR || exit

    echo "👉 Masukkan BOT TOKEN:"
    read BOT_TOKEN
    echo "👉 Masukkan CHAT ID admin (pisahkan dengan koma jika lebih dari satu):"
    read CHAT_IDS
    echo "👉 Interval scan dalam detik [15]:"
    read SCAN_INTERVAL
    [ -z "$SCAN_INTERVAL" ] && SCAN_INTERVAL=15

    CHAT_IDS_JSON=$(echo "$CHAT_IDS" | sed 's/,/","/g')
    CHAT_IDS_JSON="[$(echo "\"$CHAT_IDS_JSON\"")]"

    cat > config.json <<EOF
{
  "bot_token": "$BOT_TOKEN",
  "chat_ids": $CHAT_IDS_JSON,
  "scan_interval": $SCAN_INTERVAL
}
EOF

    [ ! -f devices.json ] && echo "{}" > devices.json
    mkdir -p backup

# === 2. Upgrade ===
elif [ "$OPT" = "2" ]; then
    echo "👉 Upgrade TeleMonitor..."
    cd $BOT_DIR || exit
    git reset --hard
    git pull origin main

    opkg update
    opkg install python3 python3-pip git-core ca-certificates
    pip3 install --upgrade pip
    pip3 install python-telegram-bot --break-system-packages

    echo "✅ Config.json dan devices.json dipertahankan"

# === 3. Reinstall Bersih ===
elif [ "$OPT" = "3" ]; then
    echo "👉 Hapus instalasi lama..."
    /etc/init.d/telemon stop 2>/dev/null
    /etc/init.d/telemon disable 2>/dev/null
    rm -rf $BOT_DIR
    rm -f $INIT_FILE

    echo "👉 Jalankan lagi script ini untuk install baru."
    exit 0
fi

# === Buat init script ===
cat > $INIT_FILE <<EOL
#!/bin/sh /etc/rc.common
# Init script OpenWrt TeleMonitor
START=99
STOP=10

USE_PROCD=1
PROG="/usr/bin/python3"
ARGS="$BOT_DIR/bot.py"

start_service() {
    procd_open_instance
    procd_set_param command \$PROG \$ARGS
    procd_set_param respawn
    procd_close_instance
}
EOL
chmod +x $INIT_FILE
/etc/init.d/telemon enable

echo "✅ Setup selesai!"
echo "👉 Jalankan manual dengan: python3 $BOT_DIR/bot.py"
echo "👉 Atau start service: /etc/init.d/telemon start"
