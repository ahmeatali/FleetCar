# Ortak kütüphane ve kod düzeni

15 Ekim 2026. Bu çalışma API sözleşmelerini, mevcut müşteri/tedarikçi kapsamını ve ticari iş akışlarını koruyarak tekrarları azaltır. Görsel düzen için mevcut ekran sınıfları korunmuştur; ortak bileşenler yerel Vue kütüphanesinden açık importlarla kullanılır. Yeni bir UI framework'ü eklenmedi.

## Frontend katmanları

| Yer | Sorumluluk |
|---|---|
| `src/components/ui/index.js` | Kararlı ortak UI giriş noktası |
| `UiButton` | Native buton, disabled/loading, erişilebilir busy durumu, varyant/boyut ve DOM focus köprüsü |
| `UiField` | Native label, kontrol kimliği, hint/hata bağlantısı; mevcut iç içe input/select alanları desteklenir |
| `UiModal` | Escape, odak çevrimi/geri dönüşü, busy durumunda kapanmama, iç içe modal sırası ve scroll kilidi |
| `UiAlert` | Hata/başarı/bilgi durumları için ortak canlı bölge semantiği |
| `UiTable` | Native tabloyu koruyan yatay kaydırma kapsayıcısı |
| `components/auth/PartnerLogin.vue` | Servis ve tedarikçi için aynı giriş/şifre sıfırlama/doğrulama ekranı |
| `api/session.js` | Portal türüne göre token seçimi; token otomatik olarak yalnız aynı origin `/api/` isteklerine eklenir |
| `api/http.js` | JSON/native body ayrımı, response kontrolü, status taşıyan ApiError; örtülü mutation retry yok |
| `api/clients.js` | Supplier/customer/legacy portal istemcileri |
| `api/partnerSession.js` | Sunucudan doğrulanan kimliğin yerel oturum metadatasına yazılması; varsayılan hesap kimliği üretmez |
| `utils/downloads.js` | Binary indirme, CSV escaping ve formül enjeksiyonu önlemi |
| `utils/formatters.js` | Türkçe tarih/sayı/para/dosya boyutu sunumu; bilinmeyen veri ile gerçek sıfırı ayırır |
| `composables/usePagination.js` | Tekrarlanan sayfalama, boş durum ve veri azalınca sayfa sınırlandırma |

Ekranlar API isteklerinin hata çözümlemesini veya CSV/Blob indirme kodunu yeniden yazmaz. Oturum/rol bilgisi istemcide yalnız görünüm içindir; yetki sunucuda uygulanır.

### Buton ve alan

```vue
<script setup>
import { UiButton, UiField } from '../components/ui/index.js'
</script>

<template>
  <UiField
    v-slot="field"
    label="Plaka"
    input-id="vehicle-plate"
    :error="errors.plate"
    required
  >
    <input
      :id="field.id"
      v-model="form.plate"
      :aria-invalid="field.invalid"
      :aria-describedby="field.describedBy"
      required
    />
  </UiField>
  <UiButton type="submit" variant="primary" :loading="saving">Kaydet</UiButton>
  <UiButton type="button" variant="secondary" @click="cancel">Vazgeç</UiButton>
</template>
```

Yeni çağrılarda `type` açıkça belirtilir. Geçiş uyumluluğu için verilmemiş `type`, eski native butonun submit davranışını korur. `class`, `style`, `aria-*`, click/klavye olayları native köke aktarılır. Eski sayfa CSS seçicileri çalışmaya devam eder; yeni tasarımlarda varyant/boyut kullanılır.

### Modal ve API

```vue
<UiModal
  v-if="editing"
  class="feature-modal-overlay"
  :busy="saving"
  label="Araç düzenle"
  @close="editing = false"
>
  <section class="feature-modal-content">...</section>
</UiModal>
```

Modal açıkken mount edilir; kapanırken `v-if` ile kaldırılır. Kütüphane overlay boyutunu veya feature tasarımını dayatmaz. İç içe modal kapanması dış modalın scroll kilidini kaldırmaz. `UiModal` içindeki yeni ekranlar ayrıca Escape/focus trap kodu yazmaz.

```javascript
import { supplierClient } from '../api/clients.js'
import { downloadApi, downloadCsv } from '../utils/downloads.js'

const record = await supplierClient('/records/offer', {
  method: 'POST',
  body: { title, customer_id, vehicle_id, date, amount, details },
})

await downloadApi('/api/supplier-workspace/reports/fleet?format=xlsx', {
  account: 'supplier',
  filename: 'filo.xlsx',
})

downloadCsv([['Plaka', 'Tutar'], ...rows], 'filo.csv')
```

`supplierApi.js` eski importlar için ince uyumluluk katmanıdır. `portalFetch.js` henüz taşınmamış eski fetch çağrılarına aynı oturum kuralını uygular; tekrar kurulması çift wrapper oluşturmaz. Blob/FormData değişmeden iletilir. Sayfa abort signal verirse taşınır; ağ hataları veya POST istekleri kendiliğinden tekrar denenmez.

## Backend katmanları

| Yer | Sorumluluk |
|---|---|
| `common/time.py` | UTC kayıt zamanı, Türkiye iş günü, tarihli tahsis aralığı |
| `common/security.py` | Opaque session üretimi, token özeti, fail-closed süre denetimi |
| `common/validation.py` | Ortak Pydantic/HTTP doğrulaması ve sonlu sayısal detay okuma |
| `supplier_context.py` | Kiralayan oturumu, rol ve şirket kapsamlı araç/işlem/müşteri lookup'ları |
| `supplier_schemas.py` | Operasyon, geçiş, dönüşüm, müşteri, kullanıcı ve ayar istek şemaları |
| `supplier_workflow.py` | İş akışı durumları, geçişler, numara ön ekleri ve ayar varsayılanları |
| `supplier_service.py` | Bağlı kayıt doğrulama, kayıt üretme, poliçe yansıtma, onay kuralı ve DTO üretimi |
| `supplier_operations.py` | HTTP route orkestrasyonu; önceki importlar için açık uyumluluk exportları |

`common/` router veya feature servislerini import etmez. Yeni feature kodu oturum/zaman/doğrulama yardımcılarını route modülünden almaz. Rol matrisi `supplier_permissions.py` içinde tektir; kullanılmayan ikinci WRITE_ROLES matrisi kaldırılmıştır. Tahsis aralığı mali eşleştirmede ve müşteri görünürlüğünde aynı helper'ı kullanır: tam zamanlar `[başlangıç,bitiş)`, yalnız gün içeren devirler belirsiz kalır.

Legacy `main.py` içinde hâlâ mevcut müşteri/servis route'ları ve büyük feature ekranlarında yerel sunum kodu vardır. Bunlar tamamen yeniden yazılmış kabul edilmez. Yeni ortak katman bunların kademeli olarak davranış testleriyle ayrıştırılması için sınır oluşturur; sırf satır sayısını azaltmak için `main.py` iş kuralları gizli global erişimle başka dosyalara taşınmaz.

## Kalite kapısı

```bash
python -m pip install -r backend/requirements-dev.txt
npm ci --prefix frontend
make check
```

Aktif Python ortamı farklıysa: `make check PYTHON=/path/to/venv/bin/python`. `make format` yalnız biçimlendirme yapar. ESLint tüm frontend/klavye template kodunu; Ruff tüm backend import/isim/hata sınıflarını; Prettier ve Black kaynak biçimini kontrol eder.

Regresyon kapsamı: backend iş akışı testleri; HTTP/token/body/CSV/format/sayfalama testleri; SSR bileşen testleri; izole test API ile 23 modüllü Chrome senaryosu ve ayrıca giriş/modal/odak/scroll testi. Tarayıcı testleri `tests/helpers/browserFixture.mjs` kullanır. Backend fixture sunucusu `backend/tests/supplier_workspace_preview.py` içindedir; gerçek uygulama veritabanını kullanmaz. Eşzamanlı tarayıcı istekleri için izole test verilerinin geçici SQLite kopyası ve ayrı bağlantılar kullanılır; sunucu kapanırken test veritabanı, belge ve token dosyaları temizlenir.

SSR testinin Vite önbelleği geçici ve izoledir; çalışan geliştirme sunucusunun optimize-deps dosyalarını değiştirmez. Kaynak biçimlendirmesi geniş bir diff üretir; semantik değişiklikler ortak UI/API/servis modüllerindedir. Bu çalışma canlı veri temizliğini yeniden çalıştırmaz veya üretime dağıtım yapmaz.

## Bu çalışmanın doğrulama kaydı

- Ortak kütüphane dışında native `<button>` kalmadı; 426 kullanım UiButton üzerinden çalışır. 376 UiField, 41 UiModal, 35 UiAlert ve 12 UiTable çağrısı mevcut ekranlara uygulanmıştır.
- `make check` başarılı: 85 backend testi, 27 frontend testi, tüm kaynaklar için lint/biçim kontrolü ve üretim derlemesi.
- `supplier-workspace.browser.mjs`: 23 modül, teklif/sözleşme/teslim/iade/mutabakat, müşteri kararları, rol ve mobil kontroller, CSV/XLSX/PDF indirmeleri geçti.
- `ui-library.browser.mjs`: hatalı/doğru tedarikçi girişi, servis girişi, şifre sıfırlama ekran geçişi, form label bağlantıları, Tab/Escape/focus geri dönüşü, iç içe busy modal, scroll kilidi ve bildirim butonu native ref erişimi Chrome'da doğrulandı.
- Paketlerin mevcut sürüm aralıklarındaki düzeltmeleri kilit dosyasına alındı; kurulum/audit sonucu 0 bilinen açık. Bu tarama tarihiyle sınırlı bir paket denetimidir.
- Kalan legacy ekranların yerel tasarım sınıfları ve route'ları korunur; bu kayıt bütün teknik borcun bittiği iddiası değildir.
