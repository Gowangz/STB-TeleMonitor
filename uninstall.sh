#!/bin/sh
# Uninstaller OpenWrt TeleMonitor
# Developer: @nodexservice

echo "⚠️  Proses Uninstall OpenWrt TeleMonitor"

# 1. Hentikan service jika jalan
if [ -f /etc/init.d/telemon ]; then
    echo "👉 Hentikan service..."
    /etc/init.d/telemon stop
    /etc/init.d/telemon disable
fi

# 2. Hapus init script
if [ -f /etc/init.d/telemon ]; then
    echo "👉 Hapus init script..."
    rm -f /etc/init.d/telemon
fi

# 3. Hapus folder bot
if [ -d /root/STB-TeleMonitor ]; then
    echo "👉 Hapus folder bot..."
    rm -rf /root/STB-TeleMonitor
fi

# 4. Opsional: hapus paket Python & dependensi
echo "❓ Apakah ingin hapus Python3 & pip juga? [y/N]"
read CONFIRM
if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    echo "👉 Hapus python3 & pip..."
    opkg remove python3 python3-pip
fi

echo "✅ Uninstall selesai. OpenWrt TeleMonitor sudah dihapus."
