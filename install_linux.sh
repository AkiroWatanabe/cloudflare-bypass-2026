#!/bin/bash
# ============================================================
# Cloudflare Bypass Aracı - Linux Ortam Kurulum Scripti
# Ubuntu/Debian sistemlerini destekler
# ============================================================

set -e

echo "=============================================="
echo "Cloudflare Bypass Aracı - Linux Ortam Kurulumu"
echo "=============================================="

# Root kontrolü
if [ "$EUID" -ne 0 ]; then 
    echo "[!] Lütfen root yetkisiyle çalıştırın: sudo bash install_linux.sh"
    exit 1
fi

echo "[1/5] Yazılım kaynakları güncelleniyor..."
apt-get update -qq

echo "[2/5] Sistem bağımlılıkları kuruluyor..."
apt-get install -y -qq \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    wget \
    curl \
    unzip

echo "[3/5] Google Chrome kuruluyor..."
if ! command -v google-chrome &> /dev/null; then
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt-get install -y -qq /tmp/chrome.deb || apt-get install -f -y -qq
    rm -f /tmp/chrome.deb
    echo "[+] Chrome kurulumu tamamlandı"
else
    echo "[+] Chrome zaten kurulu"
fi

echo "[4/5] Python bağımlılıkları kuruluyor..."
pip install -q seleniumbase pyvirtualdisplay

echo "[5/5] Kurulum doğrulanıyor..."
echo -n "  Chrome: "
google-chrome --version 2>/dev/null || echo "Bulunamadı"
echo -n "  Xvfb: "
which Xvfb &>/dev/null && echo "Kurulu" || echo "Kurulu değil"
echo -n "  Python: "
python3 --version

echo ""
echo "=============================================="
echo "✅ Kurulum tamamlandı!"
echo "=============================================="
echo ""
echo "Kullanım:"
echo "  python simple_bypass.py https://ornek.com"
echo ""
