#!/bin/bash
# ============================================================
# FleetCar — Custom Domain & SSL (HTTPS) Kurulum Scripti
# Kullanımı:
#   bash /opt/fleetcar/setup_domain.sh fleetrent.com.tr
# ============================================================

set -e

DOMAIN="${1:-fleetrent.com.tr}"
SERVER_IP="188.166.68.240"
APP_DIR="/opt/fleetcar"

echo "=================================================="
echo " FleetCar Domain & SSL Kurulumu — $DOMAIN"
echo "=================================================="

echo ""
echo "[1/3] Nginx konfigürasyonu $DOMAIN için güncelleniyor..."

cat > /etc/nginx/sites-available/fleetcar << NGINX
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN $SERVER_IP;

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";

    root $APP_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 60;
    }

    client_max_body_size 10M;

    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
}
NGINX

nginx -t
systemctl restart nginx

echo ""
echo "[2/3] Certbot SSL kütüphanesi kontrol ediliyor..."
if ! command -v certbot &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq certbot python3-certbot-nginx
fi

echo ""
echo "[3/3] Let's Encrypt SSL (HTTPS) sertifikası kuruluyor..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --redirect --agree-tos -m admin@$DOMAIN --non-interactive || {
    echo "⚠️ SSL sertifikası alınırken DNS henüz yayılmamış olabilir."
    echo "   DNS A kayıtları aktifleştikten sonra şu komutu çalıştırabilirsiniz:"
    echo "   certbot --nginx -d $DOMAIN -d www.$DOMAIN"
}

echo ""
echo "=================================================="
echo " ✅ DOMAIN KURULUMU TAMAMLANDI!"
echo "=================================================="
echo " 🌐 Web Sitesi:  https://$DOMAIN"
echo " 🌐 WWW Adresi:   https://www.$DOMAIN"
echo "=================================================="
