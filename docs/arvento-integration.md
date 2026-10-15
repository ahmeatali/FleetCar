# Arvento GPS bağlantısı

## Sağlayıcı sözleşmesi

Resmi kaynaklar: [GetVehicleStatus](https://ws.arvento.com/v1/report.asmx?op=GetVehicleStatus), [operasyon kataloğu](https://ws.arvento.com/v1/Report.asmx). Adaptör sabit HTTPS adresine form POST yapar; yönlendirmeyi takip etmez. Kullanıcı adı ve PIN'ler URL'ye, veritabanına, olay geçmişine veya istemciye yazılmaz. Sağlayıcı hata gövdesi kullanıcıya iletilmez.

Servis, kullanıcıya tanımlı araçların son konumlarını döndürür. Bu adaptör **GetVehicleStatus** kullanır; geçmiş rota veya CANbus raporları almaz. Bu yanıt hesabınızda odometre içermiyorsa kilometre alanını boş bırakın: yalnız konum işlenir. CANbus/OBD odometresi için sağlayıcı kataloğunda ayrı operasyonlar vardır; o operasyonları bu adaptör uygulamıyor.

## Kurulum

1. İlgili şirket kimliği için backend ortamında `ARVENTO_<supplier_id>_USERNAME`, `ARVENTO_<supplier_id>_PIN1`, `ARVENTO_<supplier_id>_PIN2` tanımlanır. Değerleri kaynak koduna/ekran görüntüsüne koymayın. Production HTTPS kurulumunda `FLEETCAR_COOKIE_SECURE=true` kullanılır.
2. Tedarikçi → Ayarlar → Entegrasyonlar → Arvento → Bağlantıyı Yönet: hesabın gerçek örnek yanıtındaki cihaz, kaynak zamanı, enlem/boylam alan adlarını girin. İsteğe bağlı kilometre alanı için metre/kilometre birimini ayrıca seçin. Dönüş XML'i .NET DataSet olmalıdır. Saat dilimi içermeyen zamanlar için fark dakika cinsinden belirtilir (Türkiye: 180); ISO dışı zamanlar Python `strptime` biçimiyle tanımlanır.
3. Cihaz kimliğini kalıcı FleetRent araç kimliğiyle eşleyin. Plaka değişikliği eşlemeyi değiştirmez. Geçmişi başka araca aktarmamak için cihaz/araç kimliğini bu sürümde yeniden bağlamak mümkün değildir; cihaz değişimi ayrı geçerlilik tarihli eşleme gerektirir ve henüz uygulanmadı.
4. “Arvento Verilerini Al” ile manuel senkronizasyon başlatılır. Zamanlayıcı/arka plan çalışanı kurulmadı. Ortam bilgileri ve alan eşlemesi olmadan canlı alma düğmesi etkinleşmez.
5. Eşlenmemiş cihazın verisi korunur. Eşleme sonrasında “Eşlemeyi Uygula” işlemi tekrar denenir. Düşen kilometre inceleme için saklanır; kilometre düzeltmesini otomatik yapmaz.

## İşleme kuralları ve kanıt

Şirket + sağlayıcı + cihaz/zaman kimliği benzersizdir. Aynı içerik tekrar geldiğinde ikinci konum/kilometre oluşmaz; aynı kimlikte farklı içerik 409 döndürür. Hatalı bir olay aynı parti içinde daha önce yapılan güncellemeleri de geri alır. Eski veriler güncel konumu değiştirmez. Kilometresi gerileyen kayıt konumu da değiştirmez. Aynı araç için şirket kapsamlı satır kilidi kullanılır; veritabanı benzersizliği tekrar kayıt oluşmasını engeller. Gerçek eşzamanlı çok sunuculu yük testi yapılmadı.

Kaynak/olay zamanı/alınma zamanı/işlenme zamanı, normalize edilmiş veri ve içerik özeti `IntegrationEvent` içinde tutulur. İşlenen konum `VehicleLocation`, kilometre `VehicleMileageRecord`, güncel kilometre ve GPS alanları ortak `Vehicle` kaydına yansır. Doğrulanmış kilometre bakım eşiğine ulaştığında AutomationRun ve bakım önerisi bir kez oluşur. Servis firması, plan tarihi, maliyet ve sonraki bakım aralığı girilip şirket sahibi onayından sonra servis işi açılır. Fatura ve tamamlanma yeni bakım eşiğini oluşturur. Bütçe aşımı ek onay ister; GPS verisi tek başına randevu veya iş emri açmaz. Bu zincir `test_maintenance_automation.py` içinde test edilir.

Testler: `backend/tests/test_supplier_integrations.py`. XML sütunları, metre dönüşümü, yerel zaman, DTD reddi, eksik alan, mükerrer/farklı içerik, eski/düşen kilometre, eşleme kuyruğu/tekrar işleme, tenant/rol, parti geri alma ve ayar koruma izole veritabanında test edildi. Test XML'i açıkça fixture'dır; canlı Arvento müşteri yanıtı değildir. Hesap ve gerçek örnek yanıt verilmediğinden canlı doğrulama yapılmadı.
