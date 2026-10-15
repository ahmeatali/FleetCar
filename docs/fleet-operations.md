# Şube günlük operasyon ve rezervasyon yönetimi

## Ekranlar

- Günlük Operasyonlar: doğrudan sol menüde. Ana sayfada bugünün ve geciken işlerin ilk beşi özetlenir.
- Rezervasyonlar: Kiralamalar grubu altında. 7, 14 veya 31 günlük araç takvimi ve ayrı rezervasyon listesi vardır.
- Şube ve Lokasyonlar: Ayarlar grubu altında. Şube adı, şehir, adres ve durum; araç için bağlı şube, güncel şube ve konum notu tutulur.

## Yetkiler ve mevcut kayıtlar

Şube oluşturma/düzenleme şirket sahibi ve filo yöneticisine açıktır. Araç lokasyonu mevcut araç yazma yetkilerini kullanır. Rezervasyon oluşturma, iptal ve sözleşmeye dönüştürme mevcut sözleşme yazma rollerini kullanır. Görevler şirket sahibi, filo yöneticisi, operasyon ve teslim/iade rolleri tarafından yönetilir. Diğer roller kayıtları okuyabilir. Sorumlu olarak yalnız aynı şirketteki aktif portal kullanıcıları seçilir.

Araçlara otomatik şube atanmaz. Mevcut araçlar atanmamış görünür; ilk rezervasyondan önce lokasyon tanımlanmalıdır. Güncel şube güncellemesi GPS verisini, araç teslimini veya ticari tahsisi değiştirmez. Rezervasyondaki farklı dönüş şubesi araç konumunu kendiliğinden taşımaz. Kullanıcı gerçek konumu şube ekranından doğrular.

Şubede bağlı araç veya açık rezervasyon varsa şube pasifleştirilemez. Kayıtlar silinmez. Yeni araçlar aynı araç listesinde görünür; lokasyon bilgisi ayrı tutulur.

## Rezervasyon kuralları

Rezervasyon bu ilk sürümde belirli bir araç içindir; grup bazında arama yapılabilir fakat plakasız kapasite rezervasyonu yoktur. Aylık kira bedeli kullanılır; günlük fiyatlandırma veya otomatik tahsilat yapılmaz.

Başlangıç ve bitiş günleri dahildir. Aynı gün dönüş/yeniden çıkış bu sürümde çakışır; saat bazında teslim tamponu henüz yoktur. Sunucu İstanbul iş gününü kullanır. Tarihler geçmişe başlayamaz ve aralık beş yılı aşamaz. Takvim sorgusu en fazla 93 günü destekler; arayüz 31 güne kadar gösterir.

Onaylı rezervasyonlar, taslak/aktif sözleşmeler (çok araçlı sözleşmeler dahil) ve gecikmiş fakat henüz iade edilmemiş kiralamalar müsaitliği engeller. Pasif, serviste, hasarlı veya satış dosyası bulunan araçlar kabul edilmez. Planlanmış fakat henüz başlamamış ve araç durumunu değiştirmemiş servis randevuları bu sürümde takvimde ayrı zaman bloğu oluşturmaz.

Rezervasyon, ilgili müşterinin şirket listesinde ve aracın güncel teslim şubesinde olmasını gerektirir. Başka bir şirketin müşteri, araç, şube veya görevi kullanılamaz.

“Sözleşme Taslağı Oluştur” aynı işlemde rezervasyonu kapatıp mevcut SupplierOperation sözleşmesini oluşturur. Aynı rezervasyon ikinci kez dönüştürülemez. Hata halinde iki değişiklik birlikte geri alınır. İmzalı belge, ticari onay, aktifleştirme ve teslim işlemleri mevcut akıştan devam eder. Rezervasyondan oluşan sözleşme iptal edilirse rezervasyon yeniden açılmaz; yeni rezervasyon oluşturulur.

Rezervasyonlar ve araç lokasyonu değişiklikleri şirket satırına koşullu olmayan bir kilit yazmasıyla serileştirilir. Bu, SQLite üzerinde FOR UPDATE desteğine bağımlı olmadan aynı aracın eşzamanlı iki rezervasyona verilmesini engeller. Sözleşme oluşturma/düzenleme/aktifleştirme de rezervasyon kontrolünü kullanır. Şube, görev, lokasyon ve rezervasyon işlemleri sürüm kontrolüyle eski formun yeni kaydı ezmesini engeller.

## Günlük işler

Teslim ve iade kayıtları, henüz teslim/iade planı oluşturulmamış aktif kiralamalar, bakım önerileri, açık servis talepleri ve onaylı rezervasyonlar mevcut kayıtlarından üretilir. Kaynak işlemin tarihi kullanılır; servis talebinde randevu tarihi yoksa talep oluşturma tarihi esas alınır. Kaynak kayıt tamamlandığında iş listeden kalkar. Aynı kayda bağlı sorumlu ve not ayrı FleetTask kaydında korunur.

Kaynak iş, görev ekranındaki durum değiştirilerek tamamlanamaz. “İşi Aç” ilgili mevcut kayıt ekranını açar; imza/kontrol listesi/mutabakat süreçleri atlanmaz. Kullanıcı ayrıca bağımsız görev açıp başlığını, son tarihini, sorumlusunu, notunu ve durumunu düzenleyebilir. Bağımsız görevin başlangıçtaki araç ve şube bağlantısı sonradan değiştirilmez.

## Veritabanı ve doğrulama

Dört yeni tablo: fleet_branches, fleet_vehicle_locations, fleet_tasks, fleet_reservations. Mevcut tablolara kolon eklenmez. Uygulama başlangıcındaki mevcut create_tables mekanizması yeni tabloları oluşturur; eski veritabanını sıfırlamak veya seed verisiyle doldurmak gerekmez.

Backend: backend/tests/test_fleet_operations.py — şirket/yetki sınırları, sürüm çakışması, pasifleştirme kısıtı, tarih ve araç uygunluğu, rezervasyon çakışması, çok araçlı sözleşme, imza akışı, başarısız dönüşüm geri alma, gecikmiş iade, kaynak görev koruması ve dosya tabanlı SQLite üzerinde iki eşzamanlı rezervasyon.

Tarayıcı: frontend/tests/fleet-planning.browser.mjs — yalnız izole supplier fixture ile çalıştırılır. FLEETRENT_E2E_WEB, FLEETRENT_E2E_API, FLEETRENT_E2E_FIXTURE, FLEETRENT_PLAYWRIGHT_PACKAGE ve FLEETRENT_CHROME değişkenleriyle test sunucuları seçilir. Şube/lokasyon, rezervasyon/sözleşme dönüşümü, görev atama/tamamlama, mobil görünüm ve görüntüleyici yetkileri doğrulanır.
