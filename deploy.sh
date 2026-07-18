#!/bin/bash
# ============================================================
# FleetCar — DigitalOcean Deploy Script
# Sunucuda root olarak tek seferlik çalıştırılır:
#   bash /tmp/deploy.sh
# ============================================================

set -e  # hata olursa dur

SERVER_IP="188.166.68.240"
REPO_URL="https://github.com/ahmeatali/FleetCar.git"
APP_DIR="/opt/fleetcar"

echo ""
echo "=================================================="
echo " FleetCar Deployment Başlıyor — $SERVER_IP"
echo "=================================================="

# ── 1. Sistem güncellemeleri & paketler ─────────────────────
echo ""
echo "[1/7] Sistem paketleri kuruluyor..."
apt-get update -qq
apt-get install -y -qq git python3 python3-pip python3-venv nginx curl

# Node.js 20 LTS kur (Ubuntu repo'sundaki genellikle eski olur)
if ! command -v node &>/dev/null || [[ "$(node -v)" < "v18" ]]; then
    echo "  → Node.js 20 kuruluyor..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &>/dev/null
    apt-get install -y -qq nodejs
fi

echo "  ✓ Python: $(python3 --version)"
echo "  ✓ Node:   $(node -v)"
echo "  ✓ npm:    $(npm -v)"
echo "  ✓ Nginx:  $(nginx -v 2>&1)"

# ── 2. Repo klonla veya güncelle ────────────────────────────
echo ""
echo "[2/7] Kod repository'den alınıyor..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git pull origin main
    echo "  ✓ Repo güncellendi (git pull)"
else
    git clone "$REPO_URL" "$APP_DIR"
    echo "  ✓ Repo klonlandı → $APP_DIR"
fi

# ── 3. Backend kurulumu ──────────────────────────────────────
echo ""
echo "[3/7] Backend (FastAPI) kuruluyor..."
cd "$APP_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q gunicorn
deactivate
echo "  ✓ Python sanal ortam & bağımlılıklar kuruldu"

# ── 4. Frontend build ────────────────────────────────────────
echo ""
echo "[4/7] Frontend build ediliyor..."
cd "$APP_DIR/frontend"
npm install --silent
npm run build
echo "  ✓ Frontend build tamamlandı → $APP_DIR/frontend/dist/"

# ── 5. systemd servis dosyası ────────────────────────────────
echo ""
echo "[5/7] systemd servisi ayarlanıyor..."
cat > /etc/systemd/system/fleetcar-backend.service << 'UNIT'
[Unit]
Description=FleetCar FastAPI Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/fleetcar/backend
ExecStart=/opt/fleetcar/backend/venv/bin/gunicorn app.main:app \
          -k uvicorn.workers.UvicornWorker \
          --bind 127.0.0.1:8000 \
          --workers 2 \
          --timeout 60 \
          --access-logfile /var/log/fleetcar-backend.log \
          --error-logfile /var/log/fleetcar-backend-error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

chown -R www-data:www-data "$APP_DIR"
systemctl daemon-reload
systemctl enable fleetcar-backend
systemctl restart fleetcar-backend
sleep 2
if systemctl is-active --quiet fleetcar-backend; then
    echo "  ✓ Backend servisi çalışıyor (port 8000)"
else
    echo "  ✗ Backend servisi başlatılamadı! Log:"
    journalctl -u fleetcar-backend -n 20 --no-pager
    exit 1
fi

# ── 6. Nginx konfigürasyonu ──────────────────────────────────
echo ""
echo "[6/7] Nginx ayarlanıyor..."
cat > /etc/nginx/sites-available/fleetcar << NGINX
server {
    listen 80;
    server_name $SERVER_IP;

    # Güvenlik başlıkları
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";

    # Frontend statik dosyalar
    root $APP_DIR/frontend/dist;
    index index.html;

    # Vue Router SPA fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API proxy
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

    # Büyük dosya yükleme limiti
    client_max_body_size 10M;

    # Gzip sıkıştırma
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
}
NGINX

# Default site'i kaldır, fleetcar'ı aktifleştir
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/fleetcar /etc/nginx/sites-enabled/fleetcar

nginx -t
systemctl enable nginx
systemctl restart nginx
echo "  ✓ Nginx başlatıldı"

# ── 7. Firewall ──────────────────────────────────────────────
echo ""
echo "[7/7] Firewall (ufw) ayarlanıyor..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
echo "  ✓ Firewall aktif (SSH + HTTP açık)"

# ── Özet ────────────────────────────────────────────────────
echo ""
echo "=================================================="
echo " ✅ DEPLOYMENT TAMAMLANDI!"
echo "=================================================="
echo ""
echo "  🌐 Site:       http://$SERVER_IP"
echo "  🔌 API:        http://$SERVER_IP/api/quotes"
echo "  📋 Admin:      http://$SERVER_IP/admin-portal"
echo "  🏢 Tedarikçi:  http://$SERVER_IP/supplier-login"
echo ""
echo "  Backend log:   journalctl -u fleetcar-backend -f"
echo "  Nginx log:     tail -f /var/log/nginx/access.log"
echo ""
