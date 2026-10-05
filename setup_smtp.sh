#!/usr/bin/env bash
# Configure SMTP for the deployed FleetRent backend without replacing its
# systemd service definition.
# Usage on the server: sudo bash /opt/fleetcar/setup_smtp.sh

set -euo pipefail

APP_DIR="/opt/fleetcar"
ENV_FILE="$APP_DIR/backend/.env"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Bu script sunucuda sudo ile çalıştırılmalıdır." >&2
    exit 1
fi

if [[ ! -d "$APP_DIR/backend" ]]; then
    echo "Backend dizini bulunamadı: $APP_DIR/backend" >&2
    exit 1
fi

read -r -p "SMTP Sunucu Adresi: " SMTP_HOST
read -r -p "SMTP Port (varsayılan 587): " SMTP_PORT
SMTP_PORT="${SMTP_PORT:-587}"
read -r -p "SMTP Kullanıcı Adı / E-posta: " SMTP_USER
read -r -s -p "SMTP Şifresi / Uygulama Şifresi: " SMTP_PASS
echo
read -r -p "Gönderen E-posta Adresi (varsayılan SMTP kullanıcısı): " SMTP_FROM
SMTP_FROM="${SMTP_FROM:-$SMTP_USER}"

if [[ -z "$SMTP_HOST" || -z "$SMTP_USER" || -z "$SMTP_PASS" ]]; then
    echo "SMTP sunucu, kullanıcı adı ve şifre boş bırakılamaz." >&2
    exit 1
fi
if [[ ! "$SMTP_PORT" =~ ^[0-9]+$ ]] || (( SMTP_PORT < 1 || SMTP_PORT > 65535 )); then
    echo "SMTP portu 1 ile 65535 arasında bir sayı olmalıdır." >&2
    exit 1
fi

TEMP_FILE="$(mktemp "$APP_DIR/backend/.env.XXXXXX")"
cleanup() { rm -f "$TEMP_FILE"; }
trap cleanup EXIT
chmod 600 "$TEMP_FILE"
cat > "$TEMP_FILE" <<ENV
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASS=$SMTP_PASS
SMTP_FROM=$SMTP_FROM
APP_BASE_URL=https://fleetrent.com.tr
ENV

if id www-data >/dev/null 2>&1; then
    chown www-data:www-data "$TEMP_FILE"
fi
mv -f "$TEMP_FILE" "$ENV_FILE"
trap - EXIT
chmod 600 "$ENV_FILE"

if systemctl is-active --quiet fleetcar-backend; then
    systemctl restart fleetcar-backend
    if ! systemctl is-active --quiet fleetcar-backend; then
        echo "SMTP kaydedildi ancak backend yeniden başlamadı. Durumu journalctl -u fleetcar-backend ile kontrol edin." >&2
        exit 1
    fi
    echo "SMTP ayarları kaydedildi; backend yeniden başlatıldı."
else
    echo "SMTP ayarları kaydedildi. fleetcar-backend servisi aktif değil; servis başlatılmadı."
fi
echo "Gizli ayarlar $ENV_FILE dosyasına erişimi kısıtlı şekilde kaydedildi."
