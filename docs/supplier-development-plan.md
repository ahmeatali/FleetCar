# Tedarikçi geliştirme planı

Ürün kararlarının kaynağı: [supplier-product-plan.md](supplier-product-plan.md).

## Uygulama sırası ve sınırlar

1. **Veri temelini kur:** SupplierCustomerLink, SupplierOperation, SupplierOperationEvent, SupplierPortalUser, SupplierSession, SupplierSetting. Yeni tablolar mevcut şemaya eklenir; veri silme veya örnek veri ekleme yok.
2. **Sunucu iş akışlarını kur:** şirket sahibi/rol doğrulaması, tedarikçi kapsamı, kayıt oluşturma/düzenleme, sürüm kontrolü, tür bazında durum geçişleri, bağlı kayıt doğrulaması, tekliften sözleşme, sözleşmeden teslimat/fatura, müşteri ataması, teslimat formu, ödeme bakiyesi, onay eşiği, olay geçmişi.
3. **Mevcut kaynakları birleştir:** ortak Vehicle/Customer/Request/File/Expense/HGS/Tire kaynakları; yeni kaydı bulunmayan eski araç sözleşmesi/poliçesi açık “Araç kaydı” kaynağıyla görünür. Yeni aktif kayıt ortak müşteri alanlarına yansır.
4. **Ortak ürün kabuğu:** bütün tedarikçi menüsü, ana sayfa, liste/sağ panel, filtreler, durum sekmeleri, CSV, tür bazında formlar. Mevcut ihale/talep sayfası `/supplier-portal/marketplace` altında korunur.
5. **Modüller:** Müşteriler, Teklifler, Sözleşmeler, Kiralamalar, Teslimatlar, Servis/Bakım, Hasar/Kaza, Sigorta/Kasko, Lastik, HGS, TPC, Yakıt, Faturalar, Muhasebe; Raporlar, Onay/Yetki, Kontrol/Tasarruf, Filo Planlama, Kullanıcılar/Ayarlar.
6. **Doğrula:** API uçtan uca ticari akış, rol/sahiplik izolasyonu, çakışma/yeniden oynatma, tarih/tutar doğrulaması, filtre ve maliyet çift sayım testleri; frontend derlemesi; masaüstü/mobil tarayıcı testi ve ekran görüntüsü incelemesi; mevcut müşteri/servis testleri.

## Teknik yerleşim

- `backend/app/supplier_operations.py`: ayrı APIRouter; iş kuralları, veri doğrulama ve gerçek kaynaklardan özet.
- `backend/app/models.py`: ilişki ve işlem tabloları; kurulum mevcut `create_tables()` akışını kullanır.
- `frontend/src/utils/supplierApi.js`: oturum başlığı, hata mesajları ve CSV; tüm yeni modüller kullanır.
- `frontend/src/utils/supplierModules.js`: menü, modül alan/kolon/durum sözlüğü; tek tasarım sistemi.
- `frontend/src/views/SupplierWorkspaceView.vue`: ana sayfa/rapor/analiz ekranları, kayıt listesi ve sağ detay paneli, gerçek işlemler ve modül formları.
- `frontend/src/components/Sidebar.vue`: paylaşılan koyu menü ve mobil çekmece; müşteri menüsü korunur.
- Mevcut `VehiclesView.vue` ve `VehicleDetailsView.vue`: ortak bilgi alanları korunur; tedarikçi bağlamı ve bağlantılar genişletilir.

## Güncel çıktı ve doğrulama

15 Ekim 2026: FR-KP-001 denetimiyle çok araçlı sözleşme, Rental/tahsis geçmişi, manuel imzalı PDF teyit kapısı, iade/mutabakat, bakım önerisi/onay/servis zinciri, tarihsel mali eşleştirme, satış dosyası, 18 rapor, XLSX/PDF, yedi rol ve yanıt audit'i eklendi. Müşteri ve tedarikçi ortak araç ticari geçmişini aynı kayıtlardan okur.

Doğrulama: **79 backend testi**, **8 frontend testi**, üretim derlemesi ve **23 modüllü Chrome** masaüstü/mobil senaryosu. Güncel kapsam ve canlı entegrasyon sınırları: [fr-kp-001-gap-audit.md](fr-kp-001-gap-audit.md).

## Testlerin tekrar çalıştırılması

1. Backend sanal ortamına `backend/requirements.txt` yüklenir; `python -m unittest discover -s backend/tests -q` çalıştırılır.
2. Frontend bağımlılıkları kurulu ortamda `npm test --prefix frontend` ve üretim build'i çalıştırılır. Depoda frontend node_modules yoksa mevcut yerel kurulumla Vite root/alias yapılandırması kullanılabilir; bu testte mevcut Vue/Vite kurulumu kullanıldı.
3. `python backend/tests/supplier_workspace_preview.py` izole fixture verilerinin geçici SQLite kopyasıyla 127.0.0.1:8088 üzerinde başlatılır. Kullanıcının uygulama veritabanını kullanmaz. Geçici fixture dosyasında yalnız test oturumları ve açıkça test olarak işaretli PDF bulunur.
4. Frontend geliştirme sunucusu 127.0.0.1:5188'de çalıştırılır. API isteklerini tarayıcı testi 8088'e yönlendirir.
5. Playwright bulunan ortamda `node frontend/tests/supplier-workspace.browser.mjs` çalıştırılır. Harici kurulum varsa `FLEETRENT_PLAYWRIGHT_PACKAGE` paket yolu ve gerekirse `FLEETRENT_CHROME` tarayıcı yolu verilir. Web adresi `FLEETRENT_E2E_WEB`, fixture yolu iki süreçte aynı `FLEETRENT_E2E_FIXTURE`, ekran görüntüsü klasörü `FLEETRENT_E2E_OUTPUT` ile ayarlanır. Tarayıcı senaryosu 8088 API portunu kullanır.
6. Fixture sunucusu durdurulur; geçici test oturumları/PDF/screenshot dosyaları temizlenir. Üretim veritabanı veya gerçek sağlayıcı hesapları üzerinde bu senaryo çalıştırılmaz.

## Veri ve kurulum

Yeni tablolar mevcut create_tables akışı ile eklenir. Eski müşteri/sözleşme/olay kayıtları tahmin edilerek yeni ticari kayıtlara çevrilmez. Üretim öncesinde yedekli bir kopyada veri geçişi ve eşzamanlılık provası gerekir. Eski zaman damgalı tokenlar kabul edilmez; müşteri, tedarikçi, servis ve yönetici tekrar oturum açmalıdır.

Arvento: [arvento-integration.md](arvento-integration.md). ReportLab ve Türkçe TTF PDF üretimi için gereklidir; Linux'ta DejaVuSans, macOS'ta Arial otomatik aranır; diğer ortamlar `FLEETCAR_REPORT_FONT` kullanır. HTTPS üretiminde `FLEETCAR_COOKIE_SECURE=true` ayarlanır.

## Ortak kütüphane ve clean code çalışması

UI bileşenleri, API istemcileri, sunum/indirme/sayfalama yardımcıları ve backend oturum/şema/servis katmanları ayrıştırıldı. Kullanım ve yeni kod kuralları: [code-architecture.md](code-architecture.md). Güncel kalite kapısı `make check`: 85 backend testi, 27 frontend testi, ESLint/Ruff ve Prettier/Black kontrolü, üretim derlemesi. Tarayıcıda 23 modüllü ticari akışa ek olarak `frontend/tests/ui-library.browser.mjs` giriş, modal, odak ve bildirim kontrollerini yürütür. Her iki tarayıcı dosyası aynı izole fixture sunucusuyla ve aynı ortam değişkenleriyle çalışır.
