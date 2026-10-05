# STB-TeleMonitor

[**Bahasa Indonesia**](#bahasa-indonesia) | [**English**](#english)

---

## Bahasa Indonesia

STB-TeleMonitor adalah bot OpenWrt TeleMonitor berbasis Python untuk router OpenWrt. Bot ini dirancang untuk memantau status modem, koneksi Wi-Fi, memberikan notifikasi perangkat baru yang terhubung, serta melakukan reboot otomatis jika koneksi internet terputus atau sesuai jadwal.

### Fitur Utama
*   **Pemantauan Modem**: Memantau kekuatan sinyal dan status koneksi modem.
*   **Pemantauan Wi-Fi**: Menampilkan perangkat yang terhubung ke jaringan Wi-Fi Anda.
*   **Notifikasi Perangkat Baru**: Mengirimkan notifikasi instan ketika ada perangkat baru yang terhubung ke jaringan.
*   **Auto Reboot**: Melakukan reboot otomatis secara berkala atau ketika mendeteksi koneksi internet terputus.
*   **Integrasi Notifikasi**: Mengirim informasi dan peringatan langsung ke Telegram Anda.

### Persyaratan Sistem
*   Router dengan OpenWrt
*   Python 3 installed
*   Koneksi internet aktif

### Instalasi & Penggunaan
1.  Unduh repository ini ke router Anda.
2.  Jalankan skrip instalasi:
    ```bash
    sh install.sh
    ```
3.  Untuk menghapus bot, jalankan skrip uninstall:
    ```bash
    sh uninstall.sh
    ```

---

## English

STB-TeleMonitor is a Python-based OpenWrt TeleMonitor bot designed for OpenWrt routers. This bot monitors modem status, Wi-Fi connections, sends notifications when new devices connect, and triggers automatic reboots if the internet connection is lost or based on a set schedule.

### Key Features
*   **Modem Monitoring**: Monitors signal strength and modem connection status.
*   **Wi-Fi Monitoring**: Displays devices currently connected to your Wi-Fi network.
*   **New Device Notifications**: Sends instant alerts whenever a new device connects to the network.
*   **Auto Reboot**: Performs scheduled reboots or automatically reboots when internet connection loss is detected.
*   **Notification Integration**: Sends alerts and reports directly to your Telegram.

### System Requirements
*   Router running OpenWrt
*   Python 3 installed
*   Active internet connection

### Installation & Usage
1.  Download this repository to your router.
2.  Run the installation script:
    ```bash
    sh install.sh
    ```
3.  To remove the bot, run the uninstallation script:
    ```bash
    sh uninstall.sh
    ```
