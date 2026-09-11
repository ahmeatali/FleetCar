#!/bin/bash
# ============================================================
# FleetCar — SMTP E-Posta Sunucusu Yapılandırma Scripti
# Kullanımı:
#   bash /opt/fleetcar/setup_smtp.sh
# ============================================================

set -e
APP_DIR="/opt/fleetcar"
SERVICE_FILE="/etc/systemd/system/fleetcar-backend.service"

echo "=================================================="
echo " FleetCar SMTP E-Posta Yapılandırması"
echo "=================================================="
echo ""

read -p "SMTP Sunucu Adresi (Örn: smtp.yandex.com / smtp.gmail.com): " SMTP_HOST
read -p "SMTP Port (Varsayılan 587): " SMTP_PORT
SMTP_PORT=${SMTP_PORT:-587}
read -p "SMTP Kullanıcı Adı / E-posta (Örn: bilgi@fleetrent.com.tr): " SMTP_USER
read -s -p "SMTP Şifresi / Uygulama Şifresi: " SMTP_PASS
echo ""
read -p "Gönderen E-posta Adresi (Örn: noreply@fleetrent.com.tr): " SMTP_FROM
SMTP_FROM=${SMTP_FROM:-$SMTP_USER}

if [ -z "$SMTP_HOST" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASS" ]; then
    echo "❌ HATA: SMTP sunucu, kullanıcı adı ve şifre boş bırakılamaz!"
    exit 1
fi

echo ""
echo "[1/3] backend/.env dosyasına yapılandırma yazılıyor..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="$SCRIPT_DIR/backend/.env"

cat > "$ENV_FILE" << ENV
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASS=$SMTP_PASS
SMTP_FROM=$SMTP_FROM
APP_BASE_URL=https://fleetrent.com.tr
ENV
chmod 600 "$ENV_FILE"

echo "[2/3] Çevre değişkenleri $SERVICE_FILE dosyasına ekleniyor..."

cat > /etc/systemd/system/fleetcar-backend.service << SERVICE
[Unit]
Description=FleetCar FastAPI Backend Service
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
Environment="SMTP_HOST=$SMTP_HOST"
Environment="SMTP_PORT=$SMTP_PORT"
Environment="SMTP_USER=$SMTP_USER"
Environment="SMTP_PASS=$SMTP_PASS"
Environment="SMTP_FROM=$SMTP_FROM"
Environment="APP_BASE_URL=https://fleetrent.com.tr"
ExecStart=$APP_DIR/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

echo "[3/3] Systemd servisleri güncelleniyor ve backend yeniden başlatılıyor (eğer sunucudaysa)..."
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload || true
    systemctl restart fleetcar-backend || true
fi

echo ""
echo "=================================================="
echo " ✅ SMTP YAPILANDIRMASI TAMAMLANDI!"
echo "=================================================="
echo " Gönderici E-posta: $SMTP_FROM"
echo " Sunucu: $SMTP_HOST:$SMTP_PORT"
echo "=================================================="
