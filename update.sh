#!/bin/bash
# ============================================================
# FleetCar — Hızlı Güncelleme (Update) Scripti
# Kod değişikliği yaptıktan sonra sunucuyu güncellemek için:
#   bash /opt/fleetcar/update.sh
# ============================================================

set -e
APP_DIR="/opt/fleetcar"

echo "[1/3] En son kod çekiliyor..."
cd "$APP_DIR"
git pull origin main

echo "[2/3] Frontend yeniden build ediliyor..."
cd "$APP_DIR/frontend"
npm install --silent
npm run build

echo "[3/3] Backend servisi yeniden başlatılıyor..."
systemctl restart fleetcar-backend

echo ""
echo "✅ Güncelleme tamamlandı!"
echo "   http://188.166.68.240"
