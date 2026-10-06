<template>
  <div class="vehicle-detail-shell">
    <div class="portal-layout vehicle-detail-layout">
      <Sidebar />

      <main class="portal-main vehicle-details-main">
        <header class="detail-global-bar">
          <label class="detail-search"><span>⌕</span><input v-model="pageSearch" placeholder="Araç, plaka, marka, model, kullanıcı, rapor..." @keydown.enter="returnToList" /></label>
          <div class="detail-profile"><span>{{ userInitials }}</span><div><strong>{{ userName }}</strong><small>{{ companyName }} · Filo Yöneticisi</small></div><button aria-label="Profil menüsü">⌄</button></div>
        </header>

        <div class="detail-breadcrumb"><router-link to="/dashboard/vehicles">‹ Araçlar</router-link><span>›</span><span>Araç Detayı</span></div>

        <div v-if="loading" class="detail-loading">Araç bilgileri yükleniyor…</div>
        <div v-else-if="errorMessage" class="detail-error"><h2>Araç açılamadı</h2><p>{{ errorMessage }}</p><router-link class="detail-button" to="/dashboard/vehicles">Araç listesine dön</router-link></div>

        <template v-else-if="vehicle">
          <div class="detail-page-grid">
            <section class="detail-primary-column">
              <section class="detail-vehicle-card detail-panel">
                <div class="detail-card-actions"><router-link to="/dashboard/vehicles">← Geri Dön</router-link><div><button class="detail-button primary" @click="openEdit">✎ Düzenle</button><button class="detail-button" @click="showActions = !showActions">İşlemler⌄</button><div v-if="showActions" class="detail-actions-menu"><button @click="downloadReport">Araç Raporunu İndir</button><button @click="removeVehicle">Aracı Filodan Çıkar</button></div></div></div>
                <div class="detail-hero">
                  <div class="detail-hero-photo" @click="activeTab = 'photos'" :title="photos.length ? 'Fotoğraf galerisini aç' : 'Fotoğraf ekle'">
                    <img v-if="photos[0]" :src="photos[0].url" :alt="vehicle.brand + ' ' + vehicle.model" />
                    <div v-else class="detail-car-placeholder"><span>🚘</span><small>Araç fotoğrafı ekleyin</small></div>
                    <span v-if="photos.length" class="detail-photo-count">1 / {{ photos.length }}</span>
                  </div>
                  <div class="detail-hero-content">
                    <div class="detail-model-heading"><div><h1>{{ vehicle.brand }} {{ vehicle.model }}<span v-if="vehicle.version"> {{ vehicle.version }}</span></h1><span class="detail-status-pill" :class="statusTone">● {{ vehicle.is_active ? vehicle.status : 'Filodan çıkarıldı' }}</span><span class="detail-rent-pill">Uzun Dönem Kiralık</span></div></div>
                    <dl class="detail-hero-specs"><div><dt>Plaka</dt><dd>{{ vehicle.plate }}</dd></div><div><dt>Marka</dt><dd>{{ vehicle.brand || '—' }}</dd></div><div><dt>Model</dt><dd>{{ vehicle.model || '—' }}</dd></div><div><dt>Versiyon</dt><dd>{{ vehicle.version || '—' }}</dd></div><div><dt>Renk</dt><dd>{{ vehicle.color || '—' }}</dd></div><div><dt>Yıl</dt><dd>{{ vehicle.year || '—' }}</dd></div><div><dt>Motor No</dt><dd>{{ vehicle.engine_no || '—' }}</dd></div><div><dt>Şasi No</dt><dd>{{ vehicle.chassis_no || '—' }}</dd></div></dl>
                    <div class="detail-quick-links"><button @click="openLocation">⌖ Konum</button><button @click="activeTab = 'locations'">⌖ GPS</button><button @click="createRequest('yol_yardim')">♧ Yol Yardım</button><button @click="createRequest('servis')">⚒ Servis</button><button @click="activeTab = 'hgs'">▤ HGS</button><button @click="showMoreQuickActions = !showMoreQuickActions">Daha Fazla⌄</button></div>
                    <div v-if="showMoreQuickActions" class="detail-quick-more"><button @click="createRequest('servis', 'Hasar Onarım')">Hasar / Kaza Bildir</button><button @click="createRequest('lastik')">Lastik Değişimi Talebi</button><button @click="activeTab = 'fuel'">Yakıt / Gider Kaydı</button><button @click="activeTab = 'documents'">Belge Ekle</button><button @click="activeTab = 'photos'">Fotoğraf Ekle</button></div>
                  </div>
                </div>
              </section>

              <nav class="detail-tabs" aria-label="Araç detay kategorileri">
                <button v-for="tab in tabs" :key="tab.id" :class="{ selected: activeTab === tab.id }" @click="activeTab = tab.id">{{ tab.label }}</button>
              </nav>

              <section v-if="activeTab === 'general'" class="detail-general-grid">
                <article class="detail-panel detail-information-card"><h2>▦ &nbsp; Araç Bilgileri</h2><dl class="detail-information-list"><template v-for="field in generalFields" :key="field.label"><dt>{{ field.label }}</dt><dd>{{ field.value || '—' }}</dd></template></dl></article>
                <div class="detail-general-center">
                  <article class="detail-panel detail-delivery-card"><h2>♙ &nbsp; Teslim Alma Bilgileri <button class="inline-edit" @click="openEdit">Düzenle</button></h2><div class="detail-delivery-grid"><div><small>Teslim Tarihi</small><strong>{{ formatDateTime(vehicle.delivery_date) }}</strong></div><div><small>Teslim Eden</small><strong>{{ vehicle.delivered_by || '—' }}</strong></div><div><small>Teslim Alan</small><strong>{{ vehicle.received_by || '—' }}</strong></div><div><small>Teslim Yeri</small><strong>{{ vehicle.delivery_location || '—' }}</strong></div></div><div class="detail-photo-strip"><div v-for="photo in photos.slice(0, 5)" :key="photo.id" @click="activeTab = 'photos'"><img :src="photo.url" :alt="photo.original_name"></div><label v-if="photos.length < 5" class="detail-add-photo" title="Teslim fotoğrafı ekle"><span>＋ Fotoğraf</span><input type="file" accept="image/jpeg,image/png,image/webp" @change="uploadFile($event, 'photo')"></label></div><p class="detail-notes">{{ vehicle.delivery_notes || 'Araç tesliminde kaydedilmiş not bulunmuyor.' }}</p><button class="detail-outline-link" @click="activeTab = 'photos'">▣ Tüm Fotoğrafları Gör ({{ photos.length }})</button></article>
                  <article class="detail-panel detail-notes-card"><h2>▤ &nbsp; Teslim Sırasında Alınan Notlar</h2><p>{{ vehicle.delivery_notes || 'Teslim notu eklenmemiş.' }}</p><button class="inline-edit" @click="openEdit">Notları Düzenle</button></article>
                  <article class="detail-panel detail-documents-card"><div class="detail-section-heading"><h2>▤ &nbsp; Araç Belgeleri</h2><div><button class="detail-outline-link" @click="downloadAllDocuments" :disabled="!documents.length">⇩ Tüm Belgeleri İndir</button><label class="detail-button upload-compact">＋ Belge Ekle<input type="file" accept="application/pdf,image/jpeg,image/png" @change="uploadFile($event, 'document')"></label></div></div><div v-if="documents.length" class="detail-file-list"><div v-for="document in documents" :key="document.id" class="detail-file-row"><span class="detail-file-icon" :class="document.content_type === 'application/pdf' ? 'pdf' : 'image'">{{ document.content_type === 'application/pdf' ? 'PDF' : 'IMG' }}</span><span class="detail-file-name"><strong>{{ document.document_type || document.original_name }}</strong><small>{{ document.original_name }} · {{ formatBytes(document.file_size) }}<template v-if="document.expiry_date"> · Bitiş: {{ formatDate(document.expiry_date) }}</template></small></span><a class="detail-outline-link" :href="document.url" target="_blank" rel="noreferrer">◉ Görüntüle / İndir</a><button class="file-remove" aria-label="Belgeyi sil" @click="deleteFile(document)">×</button></div></div><p v-else class="detail-empty">Bu araç için henüz belge yüklenmedi. Ruhsat, sigorta poliçesi ve sözleşme dosyalarını ekleyebilirsiniz.</p></article>
                  <article class="detail-panel detail-contract-card"><h2>▣ &nbsp; Sözleşme Bilgileri</h2><div class="detail-contract-grid"><div><small>Sözleşme No</small><strong>{{ vehicle.contract_no || '—' }}</strong></div><div><small>Sözleşme Tarihi</small><strong>{{ formatDate(vehicle.contract_signed_at || vehicle.contract_start_date) }}</strong></div><div><small>Sözleşme Süresi</small><strong>{{ vehicle.contract_duration_months ? vehicle.contract_duration_months + ' Ay' : '—' }}</strong></div><div><small>Taahhüt Edilen Km</small><strong>{{ formatNumber(vehicle.contract_committed_km) }} km</strong></div><div><small>Aylık Km Limiti</small><strong>{{ formatNumber(vehicle.monthly_km_limit) }} km</strong></div><div><small>Kiralama Bedeli</small><strong>{{ formatMoney(vehicle.monthly_rent) }} / ay + KDV</strong></div><div><small>ERP ID</small><strong>{{ vehicle.erp_id || '—' }}</strong></div></div></article>
                </div>
              </section>

              <section v-else-if="activeTab === 'service'" class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>Bakım & Servis Geçmişi</h2><p>Bu araca bağlı servis, lastik ve yol yardım kayıtları.</p></div><button class="detail-button primary" @click="createRequest('servis')">＋ Servis Talebi</button></div><div v-if="serviceItems.length" class="detail-record-list"><article v-for="item in serviceItems" :key="item.id" class="detail-record"><span class="record-icon service">⚒</span><div><strong>{{ requestTitle(item) }}</strong><p>{{ item.description }}</p><small>{{ formatDateTime(item.created_at) }} · {{ item.supplier_name || 'Tedarikçi atanmadı' }}</small><div v-if="item.details?.diagnosis_notes" class="record-notes">{{ item.details.diagnosis_notes }}</div></div><span class="record-status">{{ item.status }}</span></article></div><p v-else class="detail-empty">Bu araç için servis kaydı bulunmuyor.</p></section>

              <section v-else-if="activeTab === 'fuel'" class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>Yakıt & Giderler</h2><p>Yakıt, HGS/OGS, otopark ve diğer araç giderleri.</p></div><button class="detail-button primary" @click="showExpenseForm = !showExpenseForm">＋ Gider Ekle</button></div><form v-if="showExpenseForm" class="detail-entry-form" @submit.prevent="saveExpense"><label>Gider Türü<select v-model="expenseForm.kind"><option>Yakıt</option><option>Otopark</option><option>HGS / OGS</option><option>Diğer</option></select></label><label>Tutar (TL)<input v-model.number="expenseForm.amount" type="number" min="0.01" step="0.01" required></label><label>Tarih<input v-model="expenseForm.date" type="date" required></label><label>Litre<input v-model.number="expenseForm.liters" type="number" min="0" step="0.01"></label><label>Km<input v-model.number="expenseForm.mileage" type="number" min="0" required></label><label>Açıklama<input v-model="expenseForm.note" placeholder="İstasyon veya açıklama"></label><button class="detail-button primary" :disabled="saving">{{ saving ? 'Kaydediliyor…' : 'Kaydı Kaydet' }}</button></form><div class="detail-expense-summary"><strong>{{ formatMoney(totalExpenses) }}</strong><span>{{ expenses.length }} gider kaydı</span></div><div v-if="expenses.length" class="detail-record-list"><article v-for="expense in expenses" :key="expense.id" class="detail-record"><span class="record-icon fuel">₺</span><div><strong>{{ expense.kind }}</strong><p>{{ expense.note || 'Açıklama eklenmemiş' }}<template v-if="expense.liters"> · {{ expense.liters }} L</template></p><small>{{ formatDate(expense.date) }} · {{ formatNumber(expense.mileage) }} km</small></div><b>{{ formatMoney(expense.amount) }}</b></article></div><p v-else class="detail-empty">Bu araç için henüz gider kaydı yok.</p></section>

              <section v-else-if="activeTab === 'hgs'" class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>HGS Bilgileri</h2><p>{{ vehicle.hgs_no || 'HGS numarası tanımlanmamış' }} · {{ vehicle.hgs_active ? 'Etkin' : 'Etkin değil' }}</p></div><button class="detail-button primary" @click="showHgsForm = !showHgsForm">＋ HGS İşlemi</button></div><div class="detail-expense-summary"><strong>{{ formatMoney(vehicle.hgs_balance || 0) }}</strong><span>Mevcut HGS bakiyesi</span><small>Son yükleme: {{ formatDate(vehicle.hgs_last_reload_date) }}</small></div><form v-if="showHgsForm" class="detail-entry-form" @submit.prevent="saveHgsTransaction"><label>İşlem<select v-model="hgsForm.type"><option>Yükleme</option><option>Geçiş</option></select></label><label>Tutar (TL)<input v-model.number="hgsForm.amount" type="number" min="0.01" step="0.01" required></label><label>Tarih<input v-model="hgsForm.date" type="date" required></label><label>Açıklama<input v-model="hgsForm.description" placeholder="İşlem açıklaması"></label><button class="detail-button primary" :disabled="saving">İşlemi Kaydet</button></form><div v-if="hgsTransactions.length" class="detail-record-list"><article v-for="item in hgsTransactions" :key="item.id" class="detail-record"><span class="record-icon hgs">HGS</span><div><strong>{{ item.type }}</strong><p>{{ item.description || 'HGS işlemi' }}</p><small>{{ formatDate(item.date) }} · Bakiye {{ formatMoney(item.balance) }}</small></div><b :class="item.type === 'Yükleme' ? 'positive' : 'negative'">{{ item.type === 'Yükleme' ? '+' : '−' }}{{ formatMoney(item.amount) }}</b></article></div><p v-else class="detail-empty">HGS işlem geçmişi bulunmuyor.</p></section>

              <section v-else-if="activeTab === 'roadside'" class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>Yol Yardım Geçmişi</h2><p>Bu araç için oluşturulan acil yol yardım talepleri.</p></div><button class="detail-button primary" @click="createRequest('yol_yardim')">＋ Yol Yardım Talebi</button></div><div v-if="roadsideItems.length" class="detail-record-list"><article v-for="item in roadsideItems" :key="item.id" class="detail-record"><span class="record-icon roadside">♧</span><div><strong>{{ item.description }}</strong><p>{{ item.details?.location || 'Konum bilgisi girilmemiş' }}</p><small>{{ formatDateTime(item.created_at) }}</small></div><span class="record-status">{{ item.status }}</span></article></div><p v-else class="detail-empty">Yol yardım kaydı bulunmuyor.</p></section>

              <section v-else-if="activeTab === 'documents'" class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>Araç Belgeleri</h2><p>Ruhsat, sigorta, kasko ve sözleşme dosyalarını saklayın.</p></div><label class="detail-button primary upload-compact">＋ Belge Yükle<input type="file" accept="application/pdf,image/jpeg,image/png" @change="uploadFile($event, 'document')"></label></div><div v-if="documents.length" class="detail-file-list"><div v-for="document in documents" :key="document.id" class="detail-file-row"><span class="detail-file-icon" :class="document.content_type === 'application/pdf' ? 'pdf' : 'image'">{{ document.content_type === 'application/pdf' ? 'PDF' : 'IMG' }}</span><span class="detail-file-name"><strong>{{ document.document_type || document.original_name }}</strong><small>{{ document.original_name }} · {{ formatBytes(document.file_size) }} · Yüklendi: {{ formatDateTime(document.uploaded_at) }}<template v-if="document.expiry_date"> · Bitiş: {{ formatDate(document.expiry_date) }}</template></small></span><a class="detail-outline-link" :href="document.url" target="_blank" rel="noreferrer">Görüntüle / İndir</a><button class="file-remove" @click="deleteFile(document)">×</button></div></div><p v-else class="detail-empty">Henüz belge yok. Belgeleri bu alandan ekleyebilirsiniz.</p></section>

              <section v-else-if="activeTab === 'photos'" class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>Araç Fotoğrafları</h2><p>Aracın dış ve iç fotoğraflarını görüntüleyip yönetin.</p></div><label class="detail-button primary upload-compact">＋ Fotoğraf Yükle<input type="file" accept="image/jpeg,image/png,image/webp" multiple @change="uploadFile($event, 'photo')"></label></div><div v-if="photos.length" class="detail-photo-gallery"><figure v-for="photo in photos" :key="photo.id"><a :href="photo.url" target="_blank" rel="noreferrer"><img :src="photo.url" :alt="photo.original_name"></a><figcaption><span>{{ photo.original_name }}</span><button @click="deleteFile(photo)" aria-label="Fotoğrafı sil">×</button></figcaption></figure></div><p v-else class="detail-empty">Araca henüz fotoğraf eklenmedi.</p></section>

              <section v-else-if="activeTab === 'locations'" class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>Konum Geçmişi</h2><p>{{ vehicle.gps_last_seen_at ? 'Son GPS kaydı ' + formatDateTime(vehicle.gps_last_seen_at) : 'Bu araç için henüz GPS konumu alınmamış.' }}</p></div><button class="detail-button" @click="showLocationForm = !showLocationForm">＋ Konum Kaydı</button></div><div v-if="vehicle.gps_latitude != null && vehicle.gps_longitude != null" class="detail-map-wrap"><iframe :src="mapUrl" title="Araç konumu" loading="lazy"></iframe><a :href="externalMapUrl" target="_blank" rel="noreferrer">Haritalarda Aç ↗</a></div><form v-if="showLocationForm" class="detail-entry-form" @submit.prevent="saveLocation"><label>Enlem<input v-model.number="locationForm.latitude" type="number" min="-90" max="90" step="any" required></label><label>Boylam<input v-model.number="locationForm.longitude" type="number" min="-180" max="180" step="any" required></label><label>Adres / Konum<input v-model="locationForm.label" placeholder="İstanbul, Havalimanı"></label><button class="detail-button primary">Konumu Kaydet</button></form><div v-if="locations.length" class="detail-record-list"><article v-for="location in locations" :key="location.id" class="detail-record"><span class="record-icon location">⌖</span><div><strong>{{ location.label || 'Koordinat kaydı' }}</strong><p>{{ location.latitude }}, {{ location.longitude }} · {{ location.source === 'manual' ? 'Manuel kayıt' : 'GPS' }}</p><small>{{ formatDateTime(location.recorded_at) }}</small></div><a class="detail-outline-link" :href="mapLink(location.latitude, location.longitude)" target="_blank" rel="noreferrer">Haritada Aç</a></article></div><p v-else class="detail-empty">Konum geçmişi yok. Gerçek zamanlı GPS verisi için Ayarlar bölümünden bir GPS sağlayıcısı bağlayın.</p></section>

              <section v-else class="detail-panel detail-tab-panel"><div class="detail-section-heading"><div><h2>Araç Geçmişi</h2><p>Servis, yakıt, HGS ve yol yardım kayıtlarının zaman çizelgesi.</p></div><button class="detail-button" @click="downloadReport">Rapor İndir</button></div><div v-if="timeline.length" class="detail-record-list"><article v-for="item in timeline" :key="item.key" class="detail-record"><span class="record-icon" :class="item.tone">{{ item.icon }}</span><div><strong>{{ item.title }}</strong><p>{{ item.description }}</p><small>{{ formatDateTime(item.date) }}</small></div><span class="record-status">{{ item.status }}</span></article></div><p v-else class="detail-empty">Bu araç için işlem geçmişi bulunmuyor.</p></section>
            </section>

            <aside class="detail-aside">
              <section class="detail-panel detail-condition-card"><h2>◉ &nbsp; Araç Durumu</h2><div class="detail-condition-body"><div class="usage-ring" :style="{ '--usage': usagePercent + '%' }"><div><strong>%{{ usagePercent }}</strong><small>Kullanımda</small></div></div><dl><div><dt>Son Bakım</dt><dd>{{ formatDate(vehicle.last_service_date) }}</dd></div><div><dt>Son Km</dt><dd>{{ formatNumber(vehicle.mileage) }} km</dd></div><div><dt>Bir Sonraki Bakım</dt><dd>{{ nextServiceLabel }}</dd></div><div><dt>Kasko Bitiş</dt><dd>{{ formatDate(vehicle.casco_insurance_expiry_date) }}</dd></div><div><dt>Sigorta Bitiş</dt><dd>{{ formatDate(vehicle.traffic_insurance_expiry_date) }}</dd></div><div><dt>Muayene Bitiş</dt><dd>{{ formatDate(vehicle.inspection_date) }}</dd></div></dl></div></section>
              <section class="detail-panel detail-aside-photos"><div class="detail-aside-heading"><h2>⌂ &nbsp; Fotoğraflar</h2><button @click="activeTab = 'photos'">Tümünü Gör</button></div><div v-if="photos.length" class="detail-aside-gallery"><button v-for="photo in photos.slice(0, 6)" :key="photo.id" @click="activeTab = 'photos'"><img :src="photo.url" :alt="photo.original_name"></button></div><label v-else class="detail-photo-empty">Fotoğraf yok. ＋ Fotoğraf ekle<input type="file" accept="image/jpeg,image/png,image/webp" @change="uploadFile($event, 'photo')"></label></section>
              <section class="detail-panel detail-insurance-card"><h2>⬟ &nbsp; Sigorta ve Kasko</h2><div class="detail-insurance-grid"><article><span>⬟</span><strong>Trafik Sigortası</strong><small>Poliçe: {{ vehicle.traffic_insurance_policy_no || '—' }}</small><small>Bitiş: {{ formatDate(vehicle.traffic_insurance_expiry_date) }}</small><button @click="openEdit">Detayları Düzenle</button></article><article><span>⬟</span><strong>Kasko</strong><small>Poliçe: {{ vehicle.casco_policy_no || '—' }}</small><small>Bitiş: {{ formatDate(vehicle.casco_insurance_expiry_date) }}</small><button @click="openEdit">Detayları Düzenle</button></article></div></section>
              <section class="detail-panel detail-hgs-card"><div class="detail-aside-heading"><h2>▣ &nbsp; HGS Bilgileri</h2><span class="detail-hgs-pill">HGS</span></div><dl><div><dt>HGS No</dt><dd>{{ vehicle.hgs_no || '—' }}</dd></div><div><dt>Bakiye</dt><dd>{{ formatMoney(vehicle.hgs_balance || 0) }}</dd></div><div><dt>Son Yükleme</dt><dd>{{ formatDate(vehicle.hgs_last_reload_date) }}</dd></div></dl><button class="detail-outline-link" @click="activeTab = 'hgs'">HGS İşlemleri</button></section>
              <section class="detail-panel detail-aside-history"><div class="detail-aside-heading"><h2>☷ &nbsp; Son İşlemler</h2><button @click="activeTab = 'history'">Tümü</button></div><div v-if="timeline.length" class="detail-mini-history"><article v-for="item in timeline.slice(0, 4)" :key="item.key"><span class="record-icon" :class="item.tone">{{ item.icon }}</span><div><strong>{{ item.title }}</strong><small>{{ formatDateTime(item.date) }} · {{ formatNumber(vehicle.mileage) }} km</small></div><span class="record-status">{{ item.status }}</span></article></div><p v-else class="detail-empty compact">Henüz işlem yok.</p></section>
            </aside>
          </div>
        </template>
      </main>
    </div>

    <div v-if="showEditModal" class="detail-modal-overlay" @click.self="showEditModal = false"><section class="detail-edit-modal"><div class="detail-section-heading"><div><span class="detail-eyebrow">ARAÇ KAYDI</span><h2>Araç Bilgilerini Düzenle</h2></div><button class="detail-close" @click="showEditModal = false">×</button></div><form @submit.prevent="saveVehicle"><div v-for="group in editGroups" :key="group.title" class="detail-edit-group"><h3>{{ group.title }}</h3><div class="detail-edit-grid"><label v-for="field in group.fields" :key="field.key">{{ field.label }}<input v-model="editForm[field.key]" :type="field.type || 'text'" :step="field.type === 'number' ? 'any' : undefined" :placeholder="field.placeholder || ''"></label></div></div><footer><button type="button" class="detail-button" @click="showEditModal = false">Vazgeç</button><button class="detail-button primary" :disabled="saving">{{ saving ? 'Kaydediliyor…' : 'Değişiklikleri Kaydet' }}</button></footer></form></section></div>
    <div v-if="toast" class="detail-toast" role="status">{{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'

const route = useRoute()
const router = useRouter()
const vehicle = ref(null)
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const requests = ref([])
const expenses = ref([])
const files = ref([])
const hgsTransactions = ref([])
const locations = ref([])
const detailTabs = ['general','service','fuel','hgs','roadside','documents','photos','locations','history']
const activeTab = ref(detailTabs.includes(route.query.tab) ? route.query.tab : 'general')
watch(() => route.query.tab, tab => { activeTab.value = detailTabs.includes(tab) ? tab : 'general' })
const showEditModal = ref(false)
const showActions = ref(false)
const showMoreQuickActions = ref(false)
const showExpenseForm = ref(false)
const showHgsForm = ref(false)
const showLocationForm = ref(false)
const pageSearch = ref('')
const toast = ref('')
const editForm = reactive({})
const expenseForm = reactive({ kind: 'Yakıt', amount: '', date: new Date().toISOString().slice(0, 10), liters: '', mileage: 0, note: '' })
const hgsForm = reactive({ type: 'Yükleme', amount: '', date: new Date().toISOString().slice(0, 10), description: '' })
const locationForm = reactive({ latitude: '', longitude: '', label: '' })
const tabs = [
  { id: 'general', label: 'Genel Bilgiler' }, { id: 'service', label: 'Bakım & Servis' },
  { id: 'fuel', label: 'Yakıt & Giderler' }, { id: 'hgs', label: 'HGS' },
  { id: 'roadside', label: 'Yol Yardım' }, { id: 'documents', label: 'Belgeler' },
  { id: 'photos', label: 'Fotoğraflar' }, { id: 'locations', label: 'Konum Geçmişi' },
  { id: 'history', label: 'Geçmiş' }
]

const field = (label, key) => ({ label, key, value: vehicle.value?.[key] })
const generalFields = computed(() => [
  { label: 'Durum', value: vehicle.value?.is_active ? vehicle.value.status : 'Filodan çıkarıldı' },
  field('Atanmış Kullanıcı', 'assignment_user'), field('Çalıştığı Şirket', 'operating_company'),
  field('Segment', 'vehicle_segment'), field('Araç Grubu', 'vehicle_group'), field('Plaka', 'plate'),
  { label: 'Marka / Model', value: [vehicle.value?.brand, vehicle.value?.model].filter(Boolean).join(' ') },
  field('Versiyon', 'version'), field('Renk', 'color'), field('Şasi No', 'chassis_no'),
  field('Motor No', 'engine_no'), field('Motor Gücü', 'horsepower') && { label: 'Motor Gücü', value: vehicle.value?.horsepower ? vehicle.value.horsepower + ' HP' : '' },
  field('Silindir', 'cylinder_count'), field('Yakıt Tipi', 'fuel'), field('Vites', 'transmission'),
  field('Koltuk Sayısı', 'seat_count'), field('Bagaj Hacmi', 'trunk_volume_l') && { label: 'Bagaj Hacmi', value: vehicle.value?.trunk_volume_l ? vehicle.value.trunk_volume_l + ' L' : '' },
  { label: 'Km', value: Number(vehicle.value?.mileage || 0).toLocaleString('tr-TR') + ' km' },
  field('Tescil Tarihi', 'registration_date'), field('Trafik Sigorta No', 'traffic_insurance_policy_no'),
  field('Kasko No', 'casco_policy_no'), field('Muayene Tarihi', 'inspection_date'),
  field('Lastik Ebatı', 'tire_size'), field('Trafik Sigortası Bitiş', 'traffic_insurance_expiry_date'),
  field('Kasko Bitiş', 'casco_insurance_expiry_date'), field('ERP ID', 'erp_id')
].filter(Boolean))

const editGroups = [
  { title: 'Araç ve Teknik Bilgiler', fields: [
    { label: 'Marka', key: 'brand' }, { label: 'Model', key: 'model' }, { label: 'Versiyon', key: 'version' },
    { label: 'Plaka', key: 'plate' }, { label: 'Renk', key: 'color' }, { label: 'Üretim Yılı', key: 'year', type: 'number' },
    { label: 'Segment', key: 'vehicle_segment' }, { label: 'Araç Grubu', key: 'vehicle_group' }, { label: 'Atanmış Kullanıcı', key: 'assignment_user' },
    { label: 'Çalıştığı Şirket', key: 'operating_company' }, { label: 'Motor No', key: 'engine_no' }, { label: 'Motor Gücü (HP)', key: 'horsepower', type: 'number' },
    { label: 'Silindir Sayısı', key: 'cylinder_count', type: 'number' }, { label: 'Vites', key: 'transmission' }, { label: 'Koltuk Sayısı', key: 'seat_count', type: 'number' },
    { label: 'Bagaj Hacmi (L)', key: 'trunk_volume_l', type: 'number' }, { label: 'Lastik Ebatı', key: 'tire_size' }, { label: 'Yakıt', key: 'fuel' },
    { label: 'Güncel Km', key: 'mileage', type: 'number' }, { label: 'Aylık Km Limiti', key: 'monthly_km_limit', type: 'number' },
    { label: 'Bu Ay Yapılan Km', key: 'current_month_km', type: 'number' }, { label: 'Tescil Tarihi', key: 'registration_date', type: 'date' },
    { label: 'Muayene Bitiş Tarihi', key: 'inspection_date', type: 'date' }, { label: 'Şasi No', key: 'chassis_no' }
  ] },
  { title: 'Bakım, Sigorta ve Kasko', fields: [
    { label: 'Son Bakım Tarihi', key: 'last_service_date', type: 'date' }, { label: 'Son Bakım Km', key: 'last_service_mileage', type: 'number' },
    { label: 'Sonraki Bakım Tarihi', key: 'next_service_due_date', type: 'date' }, { label: 'Sonraki Bakım Km', key: 'next_service_due_km', type: 'number' },
    { label: 'Trafik Sigortası Poliçe No', key: 'traffic_insurance_policy_no' }, { label: 'Trafik Sigortası Bitişi', key: 'traffic_insurance_expiry_date', type: 'date' },
    { label: 'Kasko Poliçe No', key: 'casco_policy_no' }, { label: 'Kasko Bitişi', key: 'casco_insurance_expiry_date', type: 'date' }
  ] },
  { title: 'Teslim ve Kiralama Sözleşmesi', fields: [
    { label: 'Teslim Tarihi', key: 'delivery_date', type: 'datetime-local' }, { label: 'Teslim Eden', key: 'delivered_by' },
    { label: 'Teslim Alan', key: 'received_by' }, { label: 'Teslim Yeri', key: 'delivery_location' },
    { label: 'Sözleşme No', key: 'contract_no' }, { label: 'Sözleşme İmza Tarihi', key: 'contract_signed_at', type: 'date' },
    { label: 'Sözleşme Süresi (Ay)', key: 'contract_duration_months', type: 'number' }, { label: 'Taahhüt Edilen Km', key: 'contract_committed_km', type: 'number' },
    { label: 'Aylık Kira (TL)', key: 'monthly_rent', type: 'number' }, { label: 'ERP ID', key: 'erp_id' },
    { label: 'Teslim Notları', key: 'delivery_notes', textarea: true }
  ] },
  { title: 'HGS ve GPS', fields: [
    { label: 'HGS No', key: 'hgs_no' }, { label: 'HGS Bakiyesi (TL)', key: 'hgs_balance', type: 'number' },
    { label: 'Son HGS Yüklemesi', key: 'hgs_last_reload_date', type: 'date' }, { label: 'HGS Etkin', key: 'hgs_active', type: 'checkbox' },
    { label: 'GPS Enlemi', key: 'gps_latitude', type: 'number' }, { label: 'GPS Boylamı', key: 'gps_longitude', type: 'number' },
    { label: 'Konum Açıklaması', key: 'gps_location_label' }
  ] }
]

const userName = localStorage.getItem('fleetcar_customer_name') || 'Filo Yöneticisi'
const userInitials = userName.split(/\s+/).map(part => part[0]).slice(0, 2).join('').toLocaleUpperCase('tr-TR')
const companyName = localStorage.getItem('fleetcar_customer_name') || 'FleetRent'
const photos = computed(() => files.value.filter(file => file.category === 'photo'))
const documents = computed(() => files.value.filter(file => file.category === 'document'))
const serviceItems = computed(() => requests.value.filter(item => ['servis', 'lastik'].includes(item.type)))
const roadsideItems = computed(() => requests.value.filter(item => item.type === 'yol_yardim'))
const totalExpenses = computed(() => expenses.value.reduce((sum, item) => sum + Number(item.amount || 0), 0))
const statusTone = computed(() => vehicle.value?.status === 'Aktif' ? 'green' : vehicle.value?.status === 'Kazalı' ? 'red' : 'amber')
const usagePercent = computed(() => {
  const current = Number(vehicle.value?.current_month_km || 0)
  const limit = Number(vehicle.value?.monthly_km_limit || 0)
  return limit > 0 ? Math.min(100, Math.round(current * 100 / limit)) : 0
})
const nextServiceLabel = computed(() => {
  if (!vehicle.value?.next_service_due_date && !vehicle.value?.next_service_due_km) return 'Planlanmadı'
  return (vehicle.value.next_service_due_date ? formatDate(vehicle.value.next_service_due_date) : '') +
    (vehicle.value.next_service_due_km ? ' (' + formatNumber(vehicle.value.next_service_due_km) + ' km)' : '')
})
const timeline = computed(() => {
  const requestEvents = requests.value.map(item => ({
    key: 'request-' + item.id, title: requestTitle(item), description: item.description || 'Araç servis kaydı',
    date: item.created_at, status: item.status, icon: item.type === 'yol_yardim' ? '♧' : '⚒',
    tone: item.type === 'yol_yardim' ? 'roadside' : 'service'
  }))
  const expenseEvents = expenses.value.map(item => ({
    key: 'expense-' + item.id, title: item.kind + ' alımı', description: formatMoney(item.amount) + (item.liters ? ' · ' + item.liters + ' L' : '') + (item.note ? ' · ' + item.note : ''),
    date: item.date, status: 'Kaydedildi', icon: '₺', tone: 'fuel'
  }))
  const hgsEvents = hgsTransactions.value.map(item => ({
    key: 'hgs-' + item.id, title: 'HGS ' + item.type.toLocaleLowerCase('tr-TR'), description: item.description || 'Bakiye ' + formatMoney(item.balance),
    date: item.date, status: 'Kaydedildi', icon: 'HGS', tone: 'hgs'
  }))
  return [...requestEvents, ...expenseEvents, ...hgsEvents].sort((a, b) => String(b.date).localeCompare(String(a.date)))
})
const mapUrl = computed(() => {
  const lat = Number(vehicle.value?.gps_latitude)
  const lon = Number(vehicle.value?.gps_longitude)
  return 'https://www.openstreetmap.org/export/embed.html?bbox=' + (lon - 0.02) + '%2C' + (lat - 0.02) + '%2C' + (lon + 0.02) + '%2C' + (lat + 0.02) + '&layer=mapnik&marker=' + lat + '%2C' + lon
})
const externalMapUrl = computed(() => mapLink(vehicle.value?.gps_latitude, vehicle.value?.gps_longitude))

function formatNumber(value) { return value == null || value === '' ? '—' : Number(value).toLocaleString('tr-TR') }
function formatMoney(value) { return value == null || value === '' ? '—' : Number(value).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 2 }) }
function formatDate(value) { if (!value) return '—'; const parsed = new Date(value); return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleDateString('tr-TR') }
function formatDateTime(value) { if (!value) return '—'; const parsed = new Date(value); return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) }
function formatBytes(bytes) { if (!bytes) return '0 B'; return bytes < 1048576 ? Math.ceil(bytes / 1024) + ' KB' : (bytes / 1048576).toFixed(1) + ' MB' }
function requestTitle(item) { return ({ servis: 'Servis', lastik: 'Lastik değişimi', yol_yardim: 'Yol yardımı', ikame_arac: 'İkame araç' }[item.type] || item.type) + ' talebi' }
function mapLink(latitude, longitude) { return 'https://www.openstreetmap.org/?mlat=' + latitude + '&mlon=' + longitude + '#map=16/' + latitude + '/' + longitude }
function returnToList() { router.push('/dashboard/vehicles?search=' + encodeURIComponent(pageSearch.value)) }
function showToast(message) { toast.value = message; window.setTimeout(() => { toast.value = '' }, 3000) }

async function loadDetails() {
  loading.value = true
  errorMessage.value = ''
  try {
    const id = encodeURIComponent(route.params.vehicleId)
    const responses = await Promise.all([
      fetch('/api/vehicles/' + id + '?customer_id=' + encodeURIComponent(localStorage.getItem('fleetcar_customer_id') || '')), fetch('/api/requests?customer_id=' + encodeURIComponent(localStorage.getItem('fleetcar_customer_id') || '')), fetch('/api/vehicle-expenses?customer_id=' + encodeURIComponent(localStorage.getItem('fleetcar_customer_id') || '')),
      fetch('/api/vehicles/' + id + '/files?customer_id=' + encodeURIComponent(localStorage.getItem('fleetcar_customer_id') || '')), fetch('/api/vehicles/' + id + '/hgs?customer_id=' + encodeURIComponent(localStorage.getItem('fleetcar_customer_id') || '')), fetch('/api/vehicles/' + id + '/locations?customer_id=' + encodeURIComponent(localStorage.getItem('fleetcar_customer_id') || ''))
    ])
    if (!responses[0].ok) throw new Error(responses[0].status === 404 ? 'Araç kaydı bulunamadı.' : 'Araç bilgileri alınamadı.')
    vehicle.value = await responses[0].json()
    requests.value = responses[1].ok ? (await responses[1].json()).filter(item => String(item.vehicle_id) === String(vehicle.value.id)) : []
    expenses.value = responses[2].ok ? (await responses[2].json()).filter(item => String(item.vehicle_id) === String(vehicle.value.id)) : []
    files.value = responses[3].ok ? await responses[3].json() : []
    hgsTransactions.value = responses[4].ok ? await responses[4].json() : []
    locations.value = responses[5].ok ? await responses[5].json() : []
    Object.assign(expenseForm, { mileage: Number(vehicle.value.mileage || 0) })
  } catch (error) {
    errorMessage.value = error.message || 'Araç bilgileri yüklenemedi.'
  } finally {
    loading.value = false
  }
}

function openEdit() {
  Object.assign(editForm, vehicle.value)
  showEditModal.value = true
}
async function saveVehicle() {
  saving.value = true
  try {
    const payload = { ...editForm }
    const numericFields = ['year', 'horsepower', 'cylinder_count', 'seat_count', 'trunk_volume_l', 'mileage', 'monthly_km_limit', 'current_month_km', 'last_service_mileage', 'next_service_due_km', 'contract_duration_months', 'contract_committed_km']
    for (const key of numericFields) payload[key] = payload[key] === '' || payload[key] == null ? null : Number(payload[key])
    for (const key of ['monthly_rent', 'hgs_balance', 'gps_latitude', 'gps_longitude']) payload[key] = payload[key] === '' || payload[key] == null ? null : Number(payload[key])
    const response = await fetch('/api/vehicles/' + encodeURIComponent(vehicle.value.id), { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Araç bilgileri kaydedilemedi.')
    vehicle.value = data
    showEditModal.value = false
    showToast('Araç bilgileri kaydedildi.')
  } catch (error) {
    showToast(error.message || 'Araç kaydedilemedi.')
  } finally {
    saving.value = false
  }
}

async function createRequest(type, serviceType = '') {
  const query = new URLSearchParams({ type, vehicle_id: vehicle.value.id })
  if (serviceType) query.set('service_type', serviceType)
  await router.push('/dashboard/requests?' + query.toString())
}

async function uploadFile(event, category) {
  const selectedFiles = [...(event.target.files || [])]
  event.target.value = ''
  for (const file of selectedFiles) {
    if (file.size > 15 * 1024 * 1024) { showToast(file.name + ': Dosya en fazla 15 MB olabilir.'); continue }
    const documentType = category === 'document' ? window.prompt('Belge türü (Ruhsat, Kasko, Trafik Sigortası, Sözleşme vb.)', file.type === 'application/pdf' ? 'Araç Belgesi' : 'Belge') : null
    if (category === 'document' && documentType === null) continue
    const expiryDate = category === 'document' ? window.prompt('Belge bitiş tarihi (YYYY-MM-DD), yoksa boş bırakın:', '') : null
    const query = new URLSearchParams({ category, original_name: file.name })
    if (documentType) query.set('document_type', documentType)
    if (expiryDate) query.set('expiry_date', expiryDate)
    try {
      const response = await fetch('/api/vehicles/' + encodeURIComponent(vehicle.value.id) + '/files?' + query.toString(), { method: 'POST', headers: { 'Content-Type': file.type }, body: file })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Dosya yüklenemedi.')
      files.value.unshift(result)
    } catch (error) { showToast(error.message || 'Dosya yüklenemedi.') }
  }
}

async function deleteFile(file) {
  if (!window.confirm('“' + file.original_name + '” dosyasını silmek istiyor musunuz?')) return
  const response = await fetch('/api/vehicles/' + encodeURIComponent(vehicle.value.id) + '/files/' + file.id, { method: 'DELETE' })
  if (response.ok) { files.value = files.value.filter(item => item.id !== file.id); showToast('Dosya silindi.') }
  else showToast('Dosya silinemedi.')
}

async function saveExpense() {
  saving.value = true
  try {
    const response = await fetch('/api/vehicle-expenses', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...expenseForm, amount: Number(expenseForm.amount), liters: expenseForm.liters ? Number(expenseForm.liters) : null, mileage: Number(expenseForm.mileage), vehicle_id: vehicle.value.id }) })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Gider kaydı eklenemedi.')
    expenses.value.unshift(result)
    showExpenseForm.value = false
    Object.assign(expenseForm, { kind: 'Yakıt', amount: '', date: new Date().toISOString().slice(0, 10), liters: '', mileage: Number(vehicle.value.mileage || 0), note: '' })
    showToast('Gider kaydı eklendi.')
  } catch (error) { showToast(error.message || 'Gider kaydedilemedi.') }
  finally { saving.value = false }
}

async function saveHgsTransaction() {
  saving.value = true
  try {
    const response = await fetch('/api/vehicles/' + encodeURIComponent(vehicle.value.id) + '/hgs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...hgsForm, amount: Number(hgsForm.amount) }) })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'HGS işlemi kaydedilemedi.')
    hgsTransactions.value.unshift(result)
    vehicle.value.hgs_balance = result.balance
    vehicle.value.hgs_active = true
    if (result.type === 'Yükleme') vehicle.value.hgs_last_reload_date = result.date
    showHgsForm.value = false
    Object.assign(hgsForm, { type: 'Yükleme', amount: '', date: new Date().toISOString().slice(0, 10), description: '' })
    showToast('HGS işlemi kaydedildi.')
  } catch (error) { showToast(error.message || 'HGS işlemi kaydedilemedi.') }
  finally { saving.value = false }
}

async function saveLocation() {
  saving.value = true
  try {
    const response = await fetch('/api/vehicles/' + encodeURIComponent(vehicle.value.id) + '/locations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ latitude: Number(locationForm.latitude), longitude: Number(locationForm.longitude), label: locationForm.label || null }) })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Konum kaydedilemedi.')
    locations.value.unshift(result)
    vehicle.value.gps_latitude = result.latitude
    vehicle.value.gps_longitude = result.longitude
    vehicle.value.gps_location_label = result.label
    vehicle.value.gps_last_seen_at = result.recorded_at
    showLocationForm.value = false
    showToast('Konum geçmişine eklendi.')
  } catch (error) { showToast(error.message || 'Konum kaydedilemedi.') }
  finally { saving.value = false }
}

function openLocation() {
  activeTab.value = 'locations'
  if (vehicle.value.gps_latitude != null && vehicle.value.gps_longitude != null) window.open(externalMapUrl.value, '_blank', 'noopener,noreferrer')
}

async function removeVehicle() {
  showActions.value = false
  if (!window.confirm(vehicle.value.plate + ' plakalı aracı filodan çıkarmak istiyor musunuz?')) return
  const reason = window.prompt('Araç çıkarma nedeni', 'Sözleşme Bitişi')
  if (reason === null) return
  const response = await fetch('/api/vehicles/' + encodeURIComponent(vehicle.value.id) + '/remove', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason }) })
  if (response.ok) { await router.push('/dashboard/vehicles?view=archived') }
  else showToast('Araç filodan çıkarılamadı.')
}

function downloadReport() {
  const fields = ['plate', 'brand', 'model', 'version', 'year', 'color', 'chassis_no', 'engine_no', 'status', 'fuel', 'transmission', 'mileage', 'monthly_km_limit', 'contract_no', 'contract_start_date', 'contract_end_date', 'hgs_no', 'hgs_balance']
  const headers = ['Plaka', 'Marka', 'Model', 'Versiyon', 'Yıl', 'Renk', 'Şasi No', 'Motor No', 'Durum', 'Yakıt', 'Vites', 'Kilometre', 'Aylık Km Limiti', 'Sözleşme No', 'Sözleşme Başlangıç', 'Sözleşme Bitiş', 'HGS No', 'HGS Bakiye']
  const values = fields.map(key => vehicle.value[key] ?? '')
  const csv = '\uFEFF' + [headers, values].map(row => row.map(item => '"' + String(item).replaceAll('"', '""') + '"').join(';')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a'); link.href = url; link.download = 'arac-' + vehicle.value.plate + '-raporu.csv'; link.click(); URL.revokeObjectURL(url)
  showActions.value = false
}

function downloadAllDocuments() {
  for (const file of documents.value) window.open(file.url, '_blank', 'noopener,noreferrer')
}

onMounted(loadDetails)
</script>

<style scoped>
.vehicle-detail-shell { min-height: 100vh; background: #f4f7fb; color: #173252; font-family: var(--font-sans); }
.vehicle-detail-layout { min-height: 100vh; }
.vehicle-details-main { padding: 0 14px 24px; background: #f4f7fb; }
.detail-global-bar { height: 44px; margin: 0 -14px 10px; padding: 6px 15px; display: flex; align-items: center; justify-content: space-between; gap: 16px; border-bottom: 1px solid #e7edf4; background: #fff; }
.detail-search { width: min(430px, 55%); display: flex; align-items: center; gap: 8px; padding: 5px 10px; border: 1px solid #edf1f6; border-radius: 7px; background: #f7f9fc; color: #6e86a3; }
.detail-search span { font-size: 18px; }.detail-search input { width: 100%; border: 0; outline: 0; background: transparent; color: #173252; font: inherit; font-size: 10px; }
.detail-profile { display: flex; align-items: center; gap: 8px; }.detail-profile > span { width: 27px; height: 27px; display: grid; place-items: center; border-radius: 50%; background: #1470e7; color: #fff; font-size: 9px; font-weight: 700; }.detail-profile div { display: grid; gap: 2px; }.detail-profile strong { font-size: 9px; }.detail-profile small { color: #8495a9; font-size: 7px; }.detail-profile button { border: 0; background: transparent; color: #7890aa; cursor: pointer; }
.detail-breadcrumb { height: 24px; display: flex; align-items: center; gap: 7px; color: #6c829c; font-size: 9px; }.detail-breadcrumb a { color: #526d8b; text-decoration: none; }.detail-breadcrumb a:hover { color: #1266dd; }
.detail-loading, .detail-error { margin: 18px 0; padding: 30px; border: 1px solid #e5ebf2; border-radius: 9px; background: #fff; color: #6e8298; font-size: 12px; }.detail-error h2 { margin-bottom: 8px; color: #173252; font-size: 16px; }.detail-error p { margin-bottom: 15px; }
.detail-page-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(270px, 30%); align-items: start; gap: 10px; }.detail-primary-column,.detail-aside { min-width: 0; display: grid; gap: 9px; align-content: start; }.detail-panel { min-width: 0; border: 1px solid #e7edf4; border-radius: 8px; background: #fff; box-shadow: 0 2px 8px rgba(34,61,91,.025); }.detail-vehicle-card { padding: 10px; }
.detail-card-actions { min-height: 24px; display: flex; align-items: center; justify-content: space-between; gap: 8px; position: relative; }.detail-card-actions > a { color: #5e7692; text-decoration: none; font-size: 8px; }.detail-card-actions > div { display: flex; gap: 5px; position: relative; }.detail-button { min-height: 27px; display: inline-flex; align-items: center; justify-content: center; padding: 5px 9px; border: 1px solid #e1e9f2; border-radius: 6px; background: #fff; color: #4d6581; font: inherit; font-size: 8px; font-weight: 650; text-decoration: none; cursor: pointer; white-space: nowrap; }.detail-button:hover { border-color: #aec9ed; background: #f8fbff; }.detail-button.primary { border-color: #1268e8; background: #1268e8; color: #fff; }.detail-button:disabled { opacity: .55; cursor: wait; }.detail-actions-menu { position: absolute; z-index: 25; top: 32px; right: 0; width: 160px; padding: 5px; border: 1px solid #e5ebf2; border-radius: 7px; background: white; box-shadow: 0 8px 25px #142b441a; }.detail-actions-menu button { width: 100%; padding: 8px; border: 0; border-radius: 5px; background: white; color: #405b79; text-align: left; font: inherit; font-size: 8px; cursor: pointer; }.detail-actions-menu button:hover { background: #f2f6fb; }
.detail-hero { display: grid; grid-template-columns: minmax(145px, 23%) minmax(0, 1fr); gap: 13px; padding-top: 6px; }.detail-hero-photo { min-height: 116px; position: relative; overflow: hidden; display: grid; place-items: center; border-radius: 6px; background: #edf2f7; cursor: pointer; }.detail-hero-photo img { width: 100%; height: 100%; min-height: 116px; position: absolute; inset: 0; object-fit: cover; }.detail-photo-count { position: absolute; bottom: 5px; right: 6px; padding: 3px 5px; border-radius: 5px; background: #101e2ebf; color: white; font-size: 7px; }.detail-car-placeholder { display: grid; justify-items: center; gap: 5px; color: #7f93a9; }.detail-car-placeholder span { font-size: 36px; }.detail-car-placeholder small { font-size: 8px; }
.detail-hero-content { min-width: 0; }.detail-model-heading { display: flex; align-items: center; justify-content: space-between; }.detail-model-heading > div { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }.detail-model-heading h1 { color: #132e4d; font-size: 14px; letter-spacing: -.02em; }.detail-status-pill,.detail-rent-pill { display: inline-flex; align-items: center; padding: 3px 6px; border-radius: 12px; background: #eaf8f1; color: #168960; font-size: 7px; white-space: nowrap; }.detail-status-pill.amber { background: #fff5e4; color: #b77a12; }.detail-status-pill.red { background: #fff0ef; color: #c54c45; }.detail-rent-pill { background: #eaf3ff; color: #3e74bc; }
.detail-hero-specs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); column-gap: 8px; row-gap: 8px; margin: 12px 0 10px; }.detail-hero-specs div { min-width: 0; }.detail-hero-specs dt { margin-bottom: 2px; color: #8496aa; font-size: 7px; }.detail-hero-specs dd { overflow: hidden; color: #334f6f; font-size: 8px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.detail-quick-links { display: flex; flex-wrap: wrap; gap: 4px; }.detail-quick-links button,.detail-quick-more button { min-height: 24px; padding: 4px 8px; border: 1px solid #e4ebf3; border-radius: 6px; background: #fff; color: #526d8c; font: inherit; font-size: 7px; cursor: pointer; }.detail-quick-links button:hover,.detail-quick-more button:hover { border-color: #a9c6ed; color: #1265d6; }.detail-quick-more { display: flex; flex-wrap: wrap; gap: 4px; padding-top: 5px; }
.detail-tabs { display: flex; overflow-x: auto; gap: 2px; border-bottom: 1px solid #e2eaf3; background: #fff; }.detail-tabs button { min-height: 32px; padding: 7px 9px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: #697f98; font: inherit; font-size: 8px; white-space: nowrap; cursor: pointer; }.detail-tabs button.selected { border-bottom-color: #1769e4; color: #1764d3; font-weight: 700; }.detail-tabs button:hover { color: #1764d3; }
.detail-general-grid { display: grid; grid-template-columns: minmax(180px, .68fr) minmax(0, 1.65fr); align-items: start; gap: 8px; }.detail-information-card,.detail-delivery-card,.detail-notes-card,.detail-documents-card,.detail-contract-card { padding: 11px; }.detail-panel h2 { color: #183959; font-size: 9px; font-weight: 750; }.detail-information-card h2 { margin-bottom: 10px; }.detail-information-list { display: grid; grid-template-columns: minmax(84px, .9fr) minmax(0, 1.1fr); gap: 6px 7px; }.detail-information-list dt { color: #8293a7; font-size: 7px; }.detail-information-list dd { overflow-wrap: anywhere; color: #3a5573; font-size: 7px; font-weight: 600; }.detail-general-center { min-width: 0; display: grid; gap: 8px; }.detail-delivery-card h2 { margin-bottom: 10px; }.detail-delivery-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }.detail-delivery-grid div,.detail-contract-grid div { min-width: 0; display: grid; align-content: start; gap: 4px; }.detail-delivery-grid small,.detail-contract-grid small { color: #8192a6; font-size: 7px; }.detail-delivery-grid strong,.detail-contract-grid strong { overflow-wrap: anywhere; color: #3b5777; font-size: 7px; font-weight: 650; }.inline-edit { float: right; border: 0; background: transparent; color: #216bd4; font: inherit; font-size: 7px; cursor: pointer; }
.detail-photo-strip { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 5px; margin-top: 11px; }.detail-photo-strip > div,.detail-add-photo { height: 55px; display: grid; place-items: center; overflow: hidden; border-radius: 4px; background: #edf2f7; cursor: pointer; }.detail-photo-strip img { width: 100%; height: 100%; object-fit: cover; }.detail-add-photo { border: 1px dashed #d6e0eb; color: #6c83a0; font-size: 7px; }.detail-add-photo input,.upload-compact input,.detail-photo-empty input { display: none; }.detail-notes { margin: 8px 0; color: #657b94; font-size: 7px; line-height: 1.5; }.detail-outline-link { display: inline-flex; align-items: center; justify-content: center; padding: 5px 8px; border: 1px solid #e3eaf3; border-radius: 5px; background: white; color: #4d6d91; font: inherit; font-size: 7px; text-decoration: none; cursor: pointer; }.detail-outline-link:hover { border-color: #a8c6ed; color: #1765d8; }.detail-notes-card { position: relative; min-height: 66px; }.detail-notes-card p { margin-top: 8px; color: #75879c; font-size: 7px; line-height: 1.45; }.detail-notes-card .inline-edit { position: absolute; right: 10px; top: 9px; }.detail-section-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; }.detail-section-heading > div:last-child,.detail-section-heading > div:nth-child(2) { display: flex; align-items: center; gap: 5px; }.detail-section-heading h2 { margin: 0; }.detail-section-heading p { margin-top: 4px; color: #7a8ea4; font-size: 7px; }.upload-compact { position: relative; overflow: hidden; }.upload-compact input { position: absolute; inset: 0; display: block; opacity: 0; cursor: pointer; }.detail-empty { padding: 16px 9px; color: #8495a8; font-size: 8px; line-height: 1.55; }.detail-contract-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 11px 8px; margin-top: 10px; }.detail-file-list { display: grid; margin-top: 10px; }.detail-file-row { display: flex; align-items: center; gap: 8px; min-width: 0; min-height: 39px; border-top: 1px solid #eff3f7; }.detail-file-icon { width: 23px; height: 25px; flex: 0 0 23px; display: grid; place-items: center; border-radius: 4px; background: #e9f0ff; color: #4075cc; font-size: 6px; font-weight: 800; }.detail-file-icon.pdf { background: #fff0ef; color: #df5651; }.detail-file-name { min-width: 0; flex: 1; display: grid; gap: 3px; }.detail-file-name strong { overflow: hidden; color: #3e5c7c; font-size: 7px; text-overflow: ellipsis; white-space: nowrap; }.detail-file-name small { overflow: hidden; color: #8b9bad; font-size: 6px; text-overflow: ellipsis; white-space: nowrap; }.file-remove { width: 19px; height: 19px; border: 0; border-radius: 50%; background: #f5f7fa; color: #8496a8; cursor: pointer; }
.detail-condition-card,.detail-aside-photos,.detail-insurance-card,.detail-hgs-card,.detail-aside-history { padding: 11px; }.detail-condition-card h2,.detail-aside-photos h2,.detail-insurance-card h2,.detail-hgs-card h2,.detail-aside-history h2 { margin-bottom: 9px; }.detail-condition-body { display: grid; grid-template-columns: minmax(65px, 35%) minmax(0, 1fr); gap: 10px; align-items: center; }.usage-ring { width: 66px; height: 66px; display: grid; place-items: center; border-radius: 50%; background: conic-gradient(#11a971 var(--usage), #e5edf4 var(--usage)); }.usage-ring > div { width: 53px; height: 53px; display: grid; align-content: center; justify-items: center; border-radius: 50%; background: white; }.usage-ring strong { color: #193b5e; font-size: 11px; }.usage-ring small { color: #7589a1; font-size: 6px; }.detail-condition-body dl,.detail-hgs-card dl { display: grid; gap: 7px; }.detail-condition-body dl div,.detail-hgs-card dl div { display: flex; justify-content: space-between; gap: 7px; }.detail-condition-body dt,.detail-hgs-card dt { color: #7d8fa3; font-size: 7px; }.detail-condition-body dd,.detail-hgs-card dd { color: #395675; font-size: 7px; font-weight: 650; text-align: right; }
.detail-aside-heading { display: flex; align-items: center; justify-content: space-between; }.detail-aside-heading h2 { margin: 0; }.detail-aside-heading > button { border: 0; background: none; color: #236dcc; font: inherit; font-size: 7px; cursor: pointer; }.detail-aside-gallery { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin-top: 9px; }.detail-aside-gallery button { height: 55px; padding: 0; overflow: hidden; border: 0; border-radius: 4px; background: #edf2f7; cursor: pointer; }.detail-aside-gallery img { width: 100%; height: 100%; object-fit: cover; }.detail-photo-empty { min-height: 47px; margin-top: 8px; display: grid; place-items: center; border: 1px dashed #d7e1ec; border-radius: 5px; color: #6e84a0; font-size: 8px; cursor: pointer; }
.detail-insurance-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }.detail-insurance-grid article { min-width: 0; display: grid; justify-items: start; gap: 4px; padding: 7px; border: 1px solid #edf1f6; border-radius: 6px; }.detail-insurance-grid article > span { width: 20px; height: 20px; display: grid; place-items: center; border-radius: 50%; background: #edf4ff; color: #3175d4; }.detail-insurance-grid strong { color: #496582; font-size: 7px; }.detail-insurance-grid small { max-width: 100%; overflow-wrap: anywhere; color: #8a9aac; font-size: 6px; }.detail-insurance-grid button { width: 100%; margin-top: 3px; border: 1px solid #e6edf4; border-radius: 4px; background: white; color: #507195; padding: 5px 2px; font: inherit; font-size: 6px; cursor: pointer; }.detail-hgs-pill { border-radius: 10px; background: #ebf8f3; color: #16936b; padding: 3px 6px; font-size: 7px; font-weight: 800; }.detail-hgs-card dl { margin: 8px 0; }.detail-mini-history { display: grid; gap: 7px; margin-top: 8px; }.detail-mini-history article { display: grid; grid-template-columns: 21px minmax(0, 1fr) auto; align-items: center; gap: 6px; }.detail-mini-history article > div { display: grid; gap: 3px; }.detail-mini-history strong { color: #48627f; font-size: 7px; }.detail-mini-history small { color: #8595a7; font-size: 6px; }.detail-mini-history .record-status { font-size: 6px; }.detail-empty.compact { padding: 8px 0; }
.detail-tab-panel { padding: 13px; min-height: 170px; }.detail-tab-panel > .detail-section-heading { margin-bottom: 10px; }.detail-record-list { display: grid; }.detail-record { display: grid; grid-template-columns: 25px minmax(0, 1fr) auto; align-items: center; gap: 9px; min-height: 48px; padding: 7px 2px; border-top: 1px solid #edf2f7; }.record-icon { width: 23px; height: 23px; display: grid; place-items: center; border-radius: 50%; background: #eaf2ff; color: #4277cf; font-size: 8px; font-weight: 750; }.record-icon.service { background: #eaf2ff; color: #3872cc; }.record-icon.fuel { background: #ebf8f1; color: #169467; }.record-icon.hgs { background: #e8f6f1; color: #128568; font-size: 6px; }.record-icon.roadside { background: #fff1e8; color: #c97530; }.record-icon.location { background: #edf3ff; color: #5578d1; }.detail-record > div { min-width: 0; }.detail-record strong { color: #365471; font-size: 8px; }.detail-record p { margin-top: 3px; color: #70859d; font-size: 7px; }.detail-record small { display: block; margin-top: 3px; color: #91a0af; font-size: 6px; }.record-status { align-self: start; margin-top: 3px; padding: 3px 6px; border-radius: 10px; background: #ecf8f1; color: #148b64; font-size: 7px; white-space: nowrap; }.detail-record > b { color: #375779; font-size: 8px; white-space: nowrap; }.detail-record > b.positive { color: #168c66; }.detail-record > b.negative { color: #bb5a53; }.record-notes { margin-top: 6px; padding: 6px; border-radius: 5px; background: #f7f9fc; color: #70839a; font-size: 7px; }
.detail-expense-summary { display: flex; align-items: center; gap: 10px; margin: 10px 0; padding: 10px; border-radius: 6px; background: #f6f9fd; }.detail-expense-summary strong { color: #1b4267; font-size: 14px; }.detail-expense-summary span,.detail-expense-summary small { color: #74889f; font-size: 8px; }.detail-entry-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin: 10px 0; padding: 11px; border: 1px solid #e7edf4; border-radius: 7px; background: #fbfcfe; }.detail-entry-form label { display: grid; gap: 4px; color: #6a8099; font-size: 7px; }.detail-entry-form input,.detail-entry-form select { width: 100%; min-width: 0; height: 28px; border: 1px solid #e1e8f0; border-radius: 5px; background: #fff; color: #35516e; padding: 5px 7px; font: inherit; font-size: 8px; }.detail-map-wrap { height: 220px; position: relative; overflow: hidden; margin: 10px 0; border-radius: 7px; background: #edf2f7; }.detail-map-wrap iframe { width: 100%; height: 100%; border: 0; }.detail-map-wrap a { position: absolute; right: 8px; top: 8px; padding: 6px; border-radius: 5px; background: white; color: #235d9e; font-size: 8px; text-decoration: none; }
.detail-photo-gallery { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 9px; margin-top: 12px; }.detail-photo-gallery figure { min-width: 0; margin: 0; overflow: hidden; border: 1px solid #e8edf3; border-radius: 7px; background: white; }.detail-photo-gallery a { display: block; height: 105px; background: #f1f5f9; }.detail-photo-gallery img { width: 100%; height: 100%; object-fit: cover; }.detail-photo-gallery figcaption { display: flex; align-items: center; justify-content: space-between; gap: 5px; padding: 6px; color: #5d748e; font-size: 7px; }.detail-photo-gallery figcaption span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.detail-photo-gallery figcaption button { border: 0; background: transparent; color: #a64e4e; cursor: pointer; }
.detail-edit-modal { width: min(760px, 100%); max-height: min(88vh, 900px); display: flex; flex-direction: column; overflow: hidden; padding: 17px; border: 1px solid #e6ecf3; border-radius: 10px; background: white; box-shadow: 0 20px 80px #091c3266; }.detail-modal-overlay { position: fixed; z-index: 500; inset: 0; display: grid; place-items: center; padding: 18px; background: #07172ab8; backdrop-filter: blur(4px); }.detail-edit-modal > .detail-section-heading { flex: 0 0 auto; padding-bottom: 11px; border-bottom: 1px solid #edf1f5; }.detail-edit-modal h2 { margin-top: 3px; color: #19395b; font-size: 14px; }.detail-close { width: 25px; height: 25px; border: 0; border-radius: 50%; background: #f2f5f8; color: #627b96; cursor: pointer; font-size: 17px; }.detail-eyebrow { color: #8798ac; font-size: 7px; font-weight: 750; letter-spacing: .08em; }.detail-edit-modal form { min-height: 0; display: flex; flex-direction: column; }.detail-edit-modal form > .detail-edit-group:first-child { margin-top: 3px; }.detail-edit-modal form { overflow-y: auto; }.detail-edit-group { padding: 11px 0; border-bottom: 1px solid #eef2f6; }.detail-edit-group h3 { margin-bottom: 9px; color: #315373; font-size: 9px; }.detail-edit-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }.detail-edit-grid label { display: grid; align-content: start; gap: 4px; color: #70849a; font-size: 7px; }.detail-edit-grid input:not([type="checkbox"]) { width: 100%; height: 29px; border: 1px solid #e1e8ef; border-radius: 5px; outline-color: #a6c5ee; background: white; color: #365573; padding: 5px 7px; font: inherit; font-size: 8px; }.detail-edit-grid input[type="checkbox"] { width: 14px; height: 14px; accent-color: #1268e8; }.detail-edit-modal form > footer { position: sticky; bottom: -1px; display: flex; justify-content: flex-end; gap: 7px; margin: 0 -2px -2px; padding: 10px 0 0; background: white; }
.detail-toast { position: fixed; z-index: 700; right: 20px; bottom: 20px; max-width: min(360px, calc(100vw - 40px)); padding: 10px 14px; border: 1px solid #dce6f0; border-radius: 7px; background: #153657; color: white; box-shadow: 0 8px 28px #102b4828; font-size: 10px; }
.detail-primary-column > .detail-tab-panel:nth-child(n) { min-width: 0; }
@media (max-width: 1150px) { .detail-page-grid { grid-template-columns: minmax(0, 1fr) 250px; gap: 7px; }.detail-hero-specs { grid-template-columns: repeat(3, minmax(0,1fr)); }.detail-general-grid { grid-template-columns: minmax(165px,.7fr) minmax(0,1.4fr); }.detail-tabs button { padding-inline: 7px; } }
@media (max-width: 920px) { :global(.portal-layout:has(.vehicle-details-main) > .portal-sidebar) { width: 100%; position: relative; height: auto; max-height: none; border-right: 0; border-bottom: 1px solid #163656; }.vehicle-detail-layout { flex-direction: column; }.vehicle-details-main { margin-left: 0; width: 100%; max-width: 100%; }.detail-page-grid { grid-template-columns: 1fr; }.detail-aside { grid-template-columns: repeat(2, minmax(0,1fr)); align-items: start; }.detail-condition-card { grid-row: span 2; } }
@media (max-width: 620px) { .vehicle-details-main { padding: 0 8px 16px; }.detail-global-bar { margin-inline: -8px; padding-inline: 8px; }.detail-profile small { display: none; }.detail-hero { grid-template-columns: 1fr; }.detail-hero-photo { min-height: 175px; }.detail-hero-photo img { min-height: 175px; }.detail-hero-specs { grid-template-columns: repeat(2,minmax(0,1fr)); }.detail-general-grid { grid-template-columns: 1fr; }.detail-information-list { grid-template-columns: minmax(125px,.8fr) 1.2fr; }.detail-aside { grid-template-columns: 1fr; }.detail-condition-card { grid-row: auto; }.detail-delivery-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }.detail-contract-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }.detail-photo-gallery { grid-template-columns: repeat(2,minmax(0,1fr)); }.detail-edit-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }.detail-entry-form { grid-template-columns: 1fr; } }
@media (max-width: 900px) { :global(.portal-layout:has(.vehicle-details-main) > .portal-main) { margin-left: 0; width: 100%; max-width: 100%; } }
</style>
