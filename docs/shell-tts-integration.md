# Shell Taşıt Tanıma bağlantısı

Kaynak: Kullanıcının sağladığı Shell TTS Web Servisleri V3.4.4 dokümanı ve [canlı WSDL](https://tts.turkiyeshell.com/TTS/TTSWebServices.asmx?WSDL). SOAP 1.1 `GetCustomerSalesTransaction_with_rid` kullanılır. Namespace ve SOAPAction: `https://tts.turkiyeshell.com`. Parametreler WSDL'deki küçük harfli isimlerle gönderilir.

## Kurulum ve kullanım

1. Backend ortamında şirket kimliğine göre `SHELL_<supplier_id>_CUST_CODE`, `SHELL_<supplier_id>_USER_ID`, `SHELL_<supplier_id>_PASSWORD` tanımlayın. Kimlik bilgileri tarayıcıya, ayar veritabanına veya hata mesajlarına aktarılmaz. Sabit HTTPS adresi kullanılır; yönlendirmeler takip edilmez.
2. Tedarikçi paneli → Ayarlar → Entegrasyonlar → Shell Taşıt Tanıma → Bağlantıyı Yönet yolunu açın. Alt müşteri kodunu (`branch_code`) kaydedin. Direkt/reseller hesaplarda boş bırakılabilir; üçüncü taraf hesaplarda Shell'in tanımladığı alt müşteri kodu gerekir.
3. Shell plakasını filo aracıyla açıkça eşleyin. Boşluklar kaldırılır ve harfler büyütülür. Eşleme şirket kapsamındadır; geçmişi korumak için başka araca taşınamaz.
4. En fazla 31 günlük aralığı seçip yakıt alımlarını getirin. Başlangıç son 15 ay içinde, bitiş en geç dün olabilir. Tarihler İstanbul saatine göredir. Shell önceki günün onaylanmış verilerini 08.30'dan itibaren sunar. Senkronizasyon manueldir.
5. Eşlenmeyen plakalar veya pasif araçlar için gider oluşturulmaz. Kayıt geçmişte bekletilir. Eşleme/araç durumu düzeltildikten sonra “Tekrar İşle” kullanılabilir.

## Kayıt kuralları

RID şirket ve sağlayıcı kapsamında benzersizdir. Aynı içerik tekrar alındığında atlanır; farklı içerik 409 döndürür ve tüm parti geri alınır. Faturası sonradan değişen aynı RID de inceleme gerektirir. Eşzamanlı tekrar işlemede olay satırı kilitlenir ve SQLite için koşullu durum güncellemesi kullanılır; senkronizasyonda benzersizlik veritabanında korunur.

Başarılı kayıt `VehicleExpense` içinde Yakıt gideri oluşturur: tarih, litre, tutar, kaynak kilometre, ürün, istasyon, `SHELL-<RID>` fiş referansı ve fatura notu. Kaynak bilgiler ve UTTS kimliği `IntegrationEvent` içinde tutulur. Kaynak kilometrenin yalnız tam kilometre kısmı gider kaydına alınır. Güncel araç kilometresi bu aktarımla değiştirilmez. Shell yakıt alımı tam depo olduğunu kanıtlamadığından tam depo işareti eklenmez.

Bu sürüm onaylı yakıt tüketimini kapsar. Gün içi geçici işlemler, fatura detay sorgusu, limit ve yakıt alım yetkisi değiştirme metotları uygulanmamıştır. Yeni veritabanı tablosu veya migration gerektirmez. Canlı hesap bilgileri olmadan müşteri verisiyle uçtan uca servis doğrulaması yapılamaz; testler izole sentetik SOAP yanıtları kullanır.
