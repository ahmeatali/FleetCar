# Bildirim Konuları

Her konu hem uygulamada (zil ve Bildirimler sayfası) hem e-postayla gönderilir. Hesap sahibi veya filo yöneticisi, **Bildirimler → Ayarlar** sayfasından her grup için uygulama içi ve e-posta bildirimini ayrı ayrı açıp kapatabilir. E-postalar hesabın kayıtlı adresine gider.

Bir değişikliği yapan hesap kendi değişikliği için bildirim almaz (örneğin teklifi gönderen tedarikçi). Onay talepleri, görev atamaları ve ekip katılımları istisnadır; bunlar aynı hesaptaki diğer kişiler içindir.

Sürücü rolündeki kullanıcılar yalnızca kendilerine atanmış aracın bildirimlerini görür.

## Müşteri Portalı

### Teklif ve Sözleşmeler

Gelen kiralama teklifleri, başlayan ve biten sözleşmeler, imza teyitleri.

- Yeni kiralama teklifi (`offer_received`)
- Sözleşme başladı (`contract_started`)
- Sözleşme bitişi yaklaşıyor (`contract_ending`)
- Belge teyidiniz bekleniyor (`signature_required`)
- Belge teyidi tamamlandı (`signature_completed`)

### Teslimat, İade ve Rezervasyon

Planlanan ve tamamlanan teslimatlar, iadeler, rezervasyonlar ve atanan araçlar.

- Teslimat planlandı (`delivery_planned`)
- Araç teslim edildi (`delivery_completed`)
- İade planlandı (`return_planned`)
- Araç iadesi tamamlandı (`return_completed`)
- Rezervasyon güncellendi (`reservation_update`)
- Filonuza araç atandı (`vehicle_assigned`)

### Servis, Lastik ve Yol Yardım

Taleplerinizin durum değişiklikleri, yol yardım ekibi ve planlanan bakımlar.

- Talep durumu değişti (`request_update`)
- Yol yardım güncellemesi (`roadside_update`)
- Bakım planlandı (`maintenance_planned`)

### Hasar ve Cezalar

Hasar dosyalarındaki gelişmeler ve araçlarınıza yansıyan cezalar.

- Hasar dosyası güncellendi (`damage_update`)
- Yeni ceza kaydı (`fine_new`)

### Fatura ve Ödemeler

Kesilen faturalar ve kaydedilen ödemeler.

- Fatura kesildi (`invoice_issued`)
- Ödeme kaydedildi (`payment_recorded`)

### Araç Hatırlatmaları

Yaklaşan muayene, sigorta ve servis tarihleri (30, 7 gün kala ve günü gelince).

- Muayene tarihi yaklaşıyor (`inspection_due`)
- Sigorta bitişi yaklaşıyor (`insurance_due`)
- Bakım zamanı yaklaşıyor (`service_due`)

### Ekip

Davet ettiğiniz kullanıcıların hesaba katılması.

- Ekibe yeni kullanıcı katıldı (`member_joined`)

### AI Önerileri

Her sabah 09:00'da, bir önceki analizde olmayan yeni AI bulguları.

- AI'ın yeni bulguları (`ai_daily`)

## Tedarikçi Portalı

### Talepler ve Teklifler

Pazaryerine düşen yeni kiralama talepleri ve tekliflerinize verilen kararlar.

- Yeni kiralama talebi (`quote_new`)
- Teklifinize karar verildi (`offer_decision`)
- Pazaryeri teklifinize karar verildi (`bid_decision`)

### Onaylar

Onayınızı bekleyen kayıtlar ve sonuçlanan onay talepleri.

- Onay bekleyen kayıt (`approval_requested`)
- Onay talebi sonuçlandı (`approval_decided`)

### Operasyon

Yeni rezervasyonlar, yaklaşan teslimat ve iadeler, atanan ve günü gelen görevler.

- Yeni rezervasyon (`reservation_new`)
- Teslimat günü yaklaştı (`delivery_due`)
- İade günü yaklaştı (`return_due`)
- Görev atandı (`task_assigned`)
- Görevin günü geldi (`task_due`)

### Sözleşme ve İmza

İmza teyitlerindeki ilerleme ve bitişi yaklaşan sözleşmeler.

- Belge teyidinde ilerleme (`signature_progress`)
- Sözleşme bitişi yaklaşıyor (`contract_ending`)

### Servis ve Bakım

Filonuzdaki araçların servis talepleri ve sistemin önerdiği bakımlar.

- Servis talebinde gelişme (`service_update`)
- Bakım önerisi (`maintenance_proposed`)

### Hasar ve Cezalar

Bildirilen hasarlar ve yeni ceza kayıtları.

- Hasar bildirildi (`damage_reported`)
- Yeni ceza kaydı (`fine_new`)

### Araç ve Poliçe Hatırlatmaları

Filonuzdaki araçların muayene ve sigorta tarihleri, bitişi yaklaşan poliçeler.

- Muayene tarihi yaklaşıyor (`inspection_due`)
- Sigorta bitişi yaklaşıyor (`insurance_due`)
- Poliçe bitişi yaklaşıyor (`policy_ending`)

### Ekip

Davet ettiğiniz kullanıcıların hesaba katılması.

- Ekibe yeni kullanıcı katıldı (`member_joined`)

### AI Önerileri

Her sabah 09:00'da, bir önceki analizde olmayan yeni AI bulguları.

- AI'ın yeni bulguları (`ai_daily`)

## Servis Portalı

### İş Talepleri

Size atanan yeni işler, yol yardım çağrıları ve mevcut işlerdeki değişiklikler.

- Yeni iş talebi (`job_new`)
- Yeni yol yardım çağrısı (`roadside_new`)
- İş talebi güncellendi (`job_update`)

### Ekip

Davet ettiğiniz kullanıcıların hesaba katılması.

- Ekibe yeni kullanıcı katıldı (`member_joined`)

## Hatırlatmaların zamanlaması

Tarihe bağlı hatırlatmalar her sabah 07:00'de (İstanbul saati) hesaplanır. Her eşik için bir kez gönderilir:

- **Muayene, trafik sigortası, kasko, sözleşme ve poliçe bitişi:** 30 gün kala, 7 gün kala ve günü gelince.
- **Planlı bakım:** 14 gün kala, 3 gün kala ve günü gelince.
- **Teslimat ve iade:** bir gün önce ve günü gelince.
- **Görevler:** son günü gelince ya da geçince.

## Sabah AI özeti

AI filo analizi her sabah 06:00'da çalışır. Saat 09:00'da bu analiz, hesabın bir önceki analiziyle karşılaştırılır. Bir bulgu, türü ve ilgili plakalar aynıysa "aynı" sayılır; AI'ın her gün farklı kelimeler kullanması yeni bulgu sayılmaz.

Yalnızca yeni bulgular bildirime ve e-postaya girer. Önce önceliği yüksek olanlar, sonra tahmini aylık etkisi büyük olanlar listelenir; en fazla 6 satır gösterilir. Yeni bulgu yoksa bildirim ve e-posta gönderilmez. Elle başlatılan analizler bu özete dahil değildir.

