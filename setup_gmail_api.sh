#!/usr/bin/env bash
# Configure Gmail API OAuth credentials for HTTPS mail delivery on DigitalOcean.
# Usage on the server: sudo bash /opt/fleetcar/setup_gmail_api.sh

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

read -r -p "Google OAuth Client ID: " GMAIL_API_CLIENT_ID
read -r -s -p "Google OAuth Client Secret: " GMAIL_API_CLIENT_SECRET
echo
read -r -s -p "Gmail API Refresh Token (gmail.send yetkili): " GMAIL_API_REFRESH_TOKEN
echo
read -r -p "Gönderici Gmail adresi veya doğrulanmış takma ad: " GMAIL_API_SENDER

if [[ -z "$GMAIL_API_CLIENT_ID" || -z "$GMAIL_API_CLIENT_SECRET" || -z "$GMAIL_API_REFRESH_TOKEN" || -z "$GMAIL_API_SENDER" ]]; then
    echo "OAuth ayarlarının tamamı zorunludur." >&2
    exit 1
fi

TEMP_FILE="$(mktemp "$APP_DIR/backend/.env.XXXXXX")"
cleanup() { rm -f "$TEMP_FILE"; }
trap cleanup EXIT
chmod 600 "$TEMP_FILE"
if [[ -f "$ENV_FILE" ]]; then
    grep -v '^GMAIL_API_' "$ENV_FILE" > "$TEMP_FILE" || true
fi
printf 'GMAIL_API_CLIENT_ID=%s\nGMAIL_API_CLIENT_SECRET=%s\nGMAIL_API_REFRESH_TOKEN=%s\nGMAIL_API_SENDER=%s\n' \
    "$GMAIL_API_CLIENT_ID" "$GMAIL_API_CLIENT_SECRET" "$GMAIL_API_REFRESH_TOKEN" "$GMAIL_API_SENDER" >> "$TEMP_FILE"
if id www-data >/dev/null 2>&1; then
    chown www-data:www-data "$TEMP_FILE"
fi
mv -f "$TEMP_FILE" "$ENV_FILE"
trap - EXIT
chmod 600 "$ENV_FILE"

systemctl restart fleetcar-backend
if ! systemctl is-active --quiet fleetcar-backend; then
    echo "Gmail API ayarları kaydedildi ancak backend yeniden başlamadı. journalctl -u fleetcar-backend ile kontrol edin." >&2
    exit 1
fi
echo "Gmail API ayarları güvenli biçimde kaydedildi; backend aktif."
