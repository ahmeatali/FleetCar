# FR-KP-001 — Gereksinim denetimi ve tamamlama kaydı

15 Ekim 2026. Kaynaklar: kullanıcının FR-KP-001 belgesi, 14 müşteri/kiralayan referans görseli ve GPS sağlayıcısı olarak Arvento kararı. Bu kayıt önceki manuel sürüm denetiminin yerini alır. Canlı sağlayıcı doğrulaması ile izole uygulama testleri ayrı değerlendirilir.

## Tamamlanan çekirdek kapsam

| Alan | Uygulanan davranış | Kanıt / kaynak |
|---|---|---|
| Ortak ürün tasarımı | Müşteri ekranıyla ortak koyu menü, üst arama, özet kartları, durum sekmeleri, filtre, liste ve sağ detay paneli; mobil menü | SupplierWorkspaceView, Sidebar; Chrome testinde 23 modül |
| Araç ve müşteri | Araç ekleme, açık müşteri tahsisi, havuza alma; müşteri ekranıyla aynı Vehicle alanları; tedarikçi yalnız yetkili müşteri ilişkilerini kullanır | test_supplier_fleet, test_portal_access |
| Teklif / talep | Eski ihale talebi ve tedarikçi teklifi ortak ticari akışa bağlanır; değişmez teklif sürümleri; müşteri revizyon/red/kabul kararı | marketplace_bridge, offer_history; ayrı müşteri oturumlu Chrome testi |
| Çok araçlı sözleşme | Tek sözleşme altında ContractVehicle, araç başına Rental ve tahsis/sürücü dönemleri; kabul edilen teklif sürümü sabitlenir | test_rental_lifecycle |
| İmzalı belge kapısı | Sürüm ve SHA256 ile bağlı özel PDF; sözleşmede kiralayan/müşteri/FleetRent, teslimatta iki firma kendi oturumlarından teyit eder; teyitsiz aktivasyon/tamamlama engellenir | signature_documents; test_signature_documents; Chrome |
| Teslim | Araç başına kontrol listesi, km, teslim alan/yer, başlangıç durum referansı, müşteri teslim formu | rental_lifecycle; backend ve Chrome |
| İade / mutabakat | Teslim referansı ile karşılaştırma, dönem km aşımı ve hasar/yakıt ek ücretleri; finans/sahip onayı; havuz/servis/satış yönü | test_rental_lifecycle |
| GPS / bakım | Arvento son konum adaptörü, açık sütun/birim/zaman eşlemesi, cihaz ilişkisi, olay kaydı; doğrulanmış km bakım önerisi üretir; onay → servis işi → fatura/tamamlama → yeni bakım eşiği | supplier_integrations, maintenance_automation testleri |
| HGS / TPC / yakıt | Olay tarihindeki tahsis/sürücü eşleştirmesi; belirsiz kayıt için gerekçeli inceleme kuyruğu; doğrulanmış müşteriye yansıtma fatura taslağı | test_event_responsibility |
| Finans / rapor | Net/vergi/brüt kontrolü; ayrı tahsilat/ödeme; kaynak gider–fatura çift sayımı engeli; araç/müşteri kârlılığı; 18 filtreli rapor; gerçek XLSX ve Türkçe PDF | test_supplier_reports; frontend 8 hesaplama testi; Chrome indirmeleri |
| İkinci el | Satış dosyası, ekspertiz/ilan/alıcı/fiyat/belge referansları; satışa ayrılmış aracı kiralamama; kesin satış ve fatura taslağı | vehicle_sales; test_vehicle_sales |
| Yetki / audit | Yedi rol, sunucuda işlem/rapor ihracı/belge denetimi; eski API ve özel dosya yollarında gerçek oturum; yanıt kodu içeren audit | supplier_permissions, portal_access, portal_audit testleri |
| Ortak araç geçmişi | Her iki panel aynı teklif/sözleşme/teslim/iade/poliçe/hasar/ceza/fatura kayıtlarından okur; müşteri yalnız kendi gönderilmiş kayıtlarını görür | VehicleBusinessHistory, test_vehicle_business_history |
| Ana sayfa | Teslim/iade/bakım/eşleştirme ikincil kartları; gerçek kayıtlar; düzenleme sırasında duraklayan 30 saniye yenileme | SupplierWorkspaceView; frontend + Chrome |

## Veri oluşumu ve bağlantıları

`Quote → SupplierBid / MarketplaceOfferLink → SupplierOperation(offer) → OfferVersion / CustomerOfferDecision → ContractOfferLink → SupplierOperation(contract) → ContractVehicle → Rental → VehicleAssignment`

`SignedDocument + SignatureEnvelope → sürüme bağlı firma teyitleri → sözleşme aktivasyonu / teslim tamamlanması`

`Rental → delivery → başlangıç durum referansı → return → mutabakat → havuz / servis / satış`

`IntegrationMapping → IntegrationEvent → VehicleLocation / VehicleMileageRecord → AutomationRun → maintenance → Request → servis faturası → bakım eşiği`

`Tarihsel tahsis + olay zamanı → EventResponsibility → yansıtma fatura taslağı → InvoiceIdentity → ayrı Payment → raporlar`

Yeni finans ve ticari kayıtlar SupplierOperation içinde tür bazında doğrulanır; bütün kavramlar ayrı SQL tablosuna taşınmış değildir. Eski servis/lastik/gider kaynakları korunur. Müşteri değişimi fiziksel araç kaydını çoğaltmaz; tahsis geçmişi korunur. Müşteri ekranında önceki müşteriye ait olay/dosya/ticari kayıtlar süzülür. Manuel eski sözleşme alanları normalize edilmiş yeni kiralamaya otomatik dönüştürülmez.

## Doğrulama

- Backend: `python -m unittest discover -s backend/tests -q` — **79 test başarılı**. İzole SQLite veritabanları kullanıldı. Eski test fixture'larında bağlantı kapanmasına ilişkin ResourceWarning var; test hatası yok.
- Frontend: `npm test --prefix frontend` — **8 test başarılı**.
- Vue/Vite üretim derlemesi başarılı; mevcut yerel Vue/Vite bağımlılıkları kullanıldı. PDF için backend requirements dosyasına ReportLab eklendi.
- Gerçek Chrome: 23 modül; teklif → sözleşme → üç taraflı belge teyidi → aktivasyon → iki taraflı teslim teyidi → müşteri teslim formu; ayrı müşteri hesabında revizyon → yeni sürüm → kabul; iade formu → inceleme → son mutabakat → havuza dönüş; fatura/tahsilat, CSV, XLSX/PDF, müşteri oluşturma, ortak araç detayı, Arvento ayarları, görüntüleyici rolü, 390px mobil menü ve yatay taşma denetimleri geçti.
- Türkçe PDF'nin çok sayfalı çıktısı render edilerek başlık, satırlar ve sayfa altları kontrol edildi. XLSX'in ZIP/OOXML yapısı ve formül enjeksiyonuna kapalı metin hücreleri test edildi.
- Canlı kullanıcı veritabanına ve dış sağlayıcılara test verisi gönderilmedi. Tarayıcıda bulunan boş iletişim alanlı eski tedarikçi kaydı hatası düzeltildi ve regresyon testi eklendi.

Tekrar çalıştırılabilir tarayıcı fixture'ı: `backend/tests/supplier_workspace_preview.py`. Tarayıcı senaryosu: `frontend/tests/supplier-workspace.browser.mjs`. Kurulum: [supplier-development-plan.md](supplier-development-plan.md).

## Açık kalan kapsam ve canlıya geçiş bağımlılıkları

1. **Arvento canlı doğrulaması:** sunucuya şirket özelinde kullanıcı/PIN bilgisi ve gerçek yanıt sütunları gerekir. GetVehicleStatus uygulanır; geçmiş rota/CANbus operasyonları ve zamanlayıcı işçisi uygulanmadı. Cihaz değişimi için tarihli yeniden eşleme ayrıca geliştirme gerektirir. Ayrıntılar: [arvento-integration.md](arvento-integration.md).
2. **Nitelikli e-imza / belge üretimi:** mevcut çözüm manuel ıslak imzalı PDF ve hesap teyididir. Elektronik imza sağlayıcısı, doğrulanmış sağlayıcı callback'i ve sağlayıcı sertifikası yoktur. Ana sözleşme/Ek-1/Ek-2 için hukuken onaylı, sürümlü belge şablonundan otomatik üretim henüz yoktur. PDF raporu veya uygulama yazdırması bu belgelerin yerine geçmez.
3. **ERP / HGS / e-Fatura / diğer sağlayıcılar:** sağlayıcı seçilmedi. Manuel kayıt, eşleştirme ve fatura taslağı hazırdır; dış sisteme yevmiye, e-Fatura gönderimi veya HGS tahsilatı uygulanmadı. Genel sağlayıcı API anahtarı yönetimi ayrıca geliştirme gerektirir.
4. **Veri geçişi / üretim işletimi:** eski sözleşme alanlarının tam ticari geçmişe dönüşümü için kontrol edilen veri geçişi gerekir. Çok sunuculu yük/eşzamanlılık testi, yedekten geri dönüş provası ve üretim gözlemlenebilirlik kurulumu bu yerel doğrulamada yapılmadı. Satır kilidi davranışı SQLite ile sunucu veritabanlarında aynı değildir.
5. **Derin ürün kapsamı:** ticari geçmiş ortak sekmede okunur; referanslardaki her alan için ayrı uzman detay sekmesi yapılmış değildir. Satış tekliflerindeki değişiklikler olay geçmişinde tutulur; bağımsız çok alıcılı teklif pazarlığı modülü yoktur. Karar/tasarruf ekranları açıklanabilir kayıt/varsayım kurallarıdır; canlı AI modeli veya otomatik gerçekleşmiş tasarruf iddiası yoktur.

FR-KP-001'in canlı entegrasyon ve bütün ayrıntıları tamamlandı olarak işaretlenmedi. Bu rapor, uygulanan ve doğrulanan çekirdeği kalan geliştirme/kurulum işlerinden ayırır.

## Sonraki bakım — ortak kütüphane

15 Ekim 2026 clean code çalışmasıyla UI/API ve backend ortak katmanları ayrıştırıldı. Güncel kalite kanıtı: 85 backend testi, 27 frontend testi, lint/biçim/üretim kontrolleri. Kapsam ve kullanım: [code-architecture.md](code-architecture.md). Önceki ürün/entegrasyon açıklarının durumu bu refactor ile değişmez.
