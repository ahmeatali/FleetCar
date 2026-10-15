# Kullanıcılar ve Yetkiler

Müşteri portalı: `/dashboard/users`. Tedarikçi portalı: `/supplier-portal/users`.

Şirket hesabı sahibi ekip üyelerini ekler, davet eder, pasife alır ve rol izinlerini düzenler. Asıl şirket hesabı kullanıcı listesinden değiştirilemez; böylece hesap sahibi erişimini kaybetmez. Eski müşteri Ayarlar > Kullanıcılar bağlantısı yeni ekrana yönlenir.

## Kullanıcı ve davet akışı

- Kullanıcı kaydı davet göndermeden de oluşturulabilir. İlk giriş için davetin kabul edilmesi gerekir; yönetici düz metin şifre oluşturmaz.
- Davetler 48 saat geçerlidir, tek kullanımlıdır ve veritabanında yalnızca token özeti saklanır. Bağlantının tokenı URL fragmentinde taşınır; sunucu erişim günlüğüne veya yönlendiren URL'ye gönderilmez.
- Davet gönderme mevcut Gmail API / SMTP altyapısını kullanır. Gönderim başarısızsa kullanıcı kaydı korunur; ekranda açık hata durumu ve yeniden gönderme/kopyalama seçenekleri görünür. Davet URL'si yalnızca oluşturma yanıtında şirket sahibine verilir; kullanıcı listesi veya aktiviteye kaydedilmez.
- Yeni davet önceki kullanılmamış bağlantıları iptal eder. Kullanıcı pasife alınırsa davetler ve oturumlar iptal edilir. Daveti kabul eden kişi şifresini kendisi belirler ve e-postası doğrulanır.
- E-posta kimliği değiştirilemez. Kullanıcı arama, rol/durum filtreleri, sayfalama, departman ve müşteri sürücüsü için araç tahsisi desteklenir.

## Roller ve izinler

Sistem rolleri mevcut iş akışlarının yetki sınırlarını korur. Özel rol şablonları bu rollerden türetilir. Görüntüleme, ekleme, düzenleme, silme/iptal, onay ve rapor indirme ayrı gösterilir. Temel iş akışının desteklemediği işlemler matris üzerinde kapalıdır; bu ekran şirket sahibine özgü onay veya yönetim işlemlerini üyelere devretmez.

Özel rol atanmış kullanıcı varsayılan olarak şablonu izler. İstenirse kullanıcıya özel bir matris kaydedilir. Rol veya kullanıcı izinleri değiştiğinde açık kullanıcı oturumları kapatılır. Sistem rolleri değiştirilemez; kopyalarından özel roller oluşturulur. Kullanıcıya atanmış rol silinemez. Sürüm bilgileri eski ekranlardan gelen güncellemeleri 409 ile reddeder.

`team_permissions.enforce_access`, hem mevcut API'lerde hem de çalışma alanı routerlarında modül/işlem iznini kontrol eder. Tanınmayan kaynaklar özel politikası olan üyeler için kapalıdır. Tedarikçinin toplu snapshot yanıtı da görüntüleme izinlerine göre süzülür. Mevcut şirket/araç/olay dönemi kapsam denetimleri ayrıca uygulanır. Modül izni bir modülün kaynaklarına erişimi yönetir; ilişkili araç kartındaki sözleşme gibi ortak özet alanlarını ayrı alan bazında maskelemez. İndirme izni sunucunun oluşturduğu rapor çıktıları içindir; görüntülenebilen verinin elle kopyalanmasını engellemez.

Yeni tablolar: `team_roles`, `team_member_access`, `team_invitations`, `team_activity`. Başlangıçtaki `create_tables` bunları ekler; mevcut kullanıcı tablolarının verisi değiştirilmez. Eski üye politikaları yönetim ekranından kaydedilene kadar mevcut rol davranışını korur.

## Doğrulama

Backend testleri: şirket kapsamı, şirket sahibi kontrolü, davet özeti/süresi/tek kullanım/yenileme/iptal, e-posta başarısızlığı, oturum iptali, rol mirası ve desteklenmeyen izinler. `frontend/tests/team-management.browser.mjs` geçici test veritabanıyla iki portalda kullanıcı, davet, rol matrisi, mobil yerleşim, API erişim reddi ve aktiviteyi doğrular. Gerçek e-posta gönderilmez.
