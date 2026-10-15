# FleetRent

Müşteri, kiralayan tedarikçi, servis ve yönetici portallarını ortak araç ve ticari kayıtlarla yöneten uygulama.

- Backend: FastAPI, SQLAlchemy ve SQLite.
- Frontend: Vue 3, Vue Router ve Vite.
- Ortak UI: `frontend/src/components/ui`; ortak HTTP istemcileri: `frontend/src/api`.

## Yerel geliştirme

Python ortamı oluşturup bağımlılıkları yükleyin:

```bash
python3 -m venv backend/venv
backend/venv/bin/python -m pip install -r backend/requirements-dev.txt
```

Backend'i `backend` klasöründen başlatın:

```bash
cd backend
venv/bin/uvicorn app.main:app --port 8000 --reload
```

SQLite dosyası `backend/fleetcar.db` altında oluşturulur. Başlangıç örnek müşteri, araç veya teklif eklemez. İlk yönetici hesabı için aynı klasörde `venv/bin/python create_admin.py` çalıştırılır; e-posta ve şifre etkileşimli sorulur.

Başka bir terminalde frontend'i başlatın:

```bash
npm ci --prefix frontend
npm run dev --prefix frontend
```

Vite `/api` ve `/uploads` yollarını varsayılan olarak `http://127.0.0.1:8000` adresine aktarır. Farklı backend için Vite sürecinde `FLEETCAR_BACKEND_URL` ayarlanır.

## Kontroller

```bash
make check PYTHON=backend/venv/bin/python
make format PYTHON=backend/venv/bin/python
```

Kontrol; ESLint, Ruff, Prettier, Black, backend/frontend testleri ve üretim derlemesini kapsar. Node ortamı, kurulu Vite ve ESLint paketlerinin engine gereksinimlerini karşılamalıdır; bu çalışma Node 24 ile doğrulandı.

## Mimari ve ürün belgeleri

- [Ortak kütüphane, katmanlar ve kullanım örnekleri](docs/code-architecture.md)
- [Ürün ve veri bağlantıları](docs/supplier-product-plan.md)
- [Geliştirme ve izole tarayıcı testleri](docs/supplier-development-plan.md)
- [FR-KP-001 kapsamı ve açık entegrasyonlar](docs/fr-kp-001-gap-audit.md)
- [Arvento kurulumu](docs/arvento-integration.md)
- [Yerel test verisi temizlik kaydı](docs/legacy-data-cleanup.md)

İmza akışı şu anda manuel imzalı PDF ve firma hesabı teyididir. Canlı Arvento hesabı ve diğer ERP/HGS/e-Fatura/e-imza sağlayıcıları ayrıca yapılandırılmalıdır. Gerçek erişim bilgileri kaynak koduna eklenmez.
