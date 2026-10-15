# Yerel test verisi temizliği — 15 Ekim 2026

İncelenen yerel uygulama veritabanı: `/Users/asd/FleetCar/backend/fleetcar.db`.
Çalışma kopyasındaki `backend/fleetcar.db` mevcut değildi; boş bir veritabanı oluşturulmadı.

## Sonuç

| Tablo | Önce | Sonra |
|---|---:|---:|
| customers | 2 | 0 |
| quotes | 9 | 0 |
| admin_users | 1 | 1 |
| customer_portal_users | 0 | 0 |
| suppliers | 0 | 0 |
| vehicles | 0 | 0 |

Test müşteri hesapları ad/e-posta/kimlik eşleşmesiyle belirlendi. Tekno Holding teklifinin de test olduğu kullanıcı tarafından ayrıca doğrulandı. Eski tarih veya pasiflik tek başına silme ölçütü yapılmadı. Mevcut yönetici satırı tüm alanlarıyla yedekle karşılaştırıldı ve değişmediği doğrulandı.

## Geri dönüş ve güvenlik

- Silmeden önce SQLite backup API ile tam yedek alındı, `integrity_check=ok` doğrulandı.
- Yedek: `backend/private-backups/fleetcar-before-cleanup-20261015T073420Z-f7ccb6bc.sqlite3`. Dosya izni `0600`; klasör Git dışında tutulur. Eski kayıtlar yalnız bu geri dönüş yedeğinde korunur.
- Temizlik tek transaction içinde yapıldı. Beklenmeyen kimlik veya bağlı iş kaydı bulunursa işlem durur; yazma hatasında tamamı geri alınır.
- Son kontrolde `integrity_check=ok`, yabancı anahtar ihlali `0`.
- Araç, servis, dosya ve finans tabloları bu veritabanında boştu; bunlardan kayıt silinmedi.
- Bu işlem yerel dosyayı kapsar. Uzak/üretim veritabanlarına bağlanılmadı.

## Kod temizliği

- Eski servis ekranındaki sabit `1.4`, `0.5`, `1.8` günlük performans değerleri kaldırıldı. Değerler artık backend'den alınan tamamlanmış servis kayıtlarının gerçek kabul/tamamlanma zamanlarından hesaplanır. Eksik, geçersiz veya ters zamanlar dışlanır; veri yoksa “Veri yok” gösterilir.
- Sunucu kaydı yokken ekranda üretilen `SERV-2026-...` iş emri numaraları kaldırıldı. Gerçek numara yoksa “Henüz oluşturulmadı” gösterilir.
- Kullanılmayan `backend/app/db.py` bellek içi mock veritabanı dosyası kaldırıldı. Uygulama gerçek SQLAlchemy veritabanını kullanır.
- Normal başlangıçtaki seed fonksiyonu örnek kayıt eklemez. İzole otomatik test fixture'ları test doğrulaması için korunur; kullanıcı veritabanına yazmaz.

## Kontroller

83 backend testi, 11 frontend testi ve Vue/Vite üretim derlemesi başarılı. Temizlik için ayrıca yedek/korunan gerçek kayıtlar, tekrar çalıştırma, kimlik değişikliği, bağlı kayıt engeli ve transaction rollback senaryoları test edildi.

Bakım aracı: `backend/maintenance/clean_legacy_test_data.py`; varsayılanı yalnız dry-run'dır. Bu çalışmada incelenen kesin kimliklere özgüdür; genel amaçlı yaşa göre kullanıcı silme aracı değildir.
