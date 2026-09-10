<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Breadcrumb -->
      <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <router-link to="/dashboard" style="color: #64748b; text-decoration: none;">← Geri</router-link>
        <span>/ Ayarlar / {{ activeTabTitle }}</span>
      </div>

      <!-- Header -->
      <header class="dashboard-header" style="margin-bottom: 25px;">
        <div>
          <h1>Sistem ve Şirket Ayarları</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Kullanıcı hesapları, araç teslim formları, bayi sözleşmeleri ve şirket evrakları.</p>
        </div>
        <button v-if="activeTab === 'kullanicilar'" @click="showAddUserModal = true" class="btn btn-blue" style="padding: 10px 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>👤</span> Yeni Kullanıcı Ekle
        </button>
        <button v-if="activeTab === 'teslim_formlari'" @click="showAddFormModal = true" class="btn btn-blue" style="padding: 10px 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>📋</span> Yeni Teslim Formu
        </button>
        <button v-if="activeTab === 'sirket_evraklari'" @click="showUploadDocModal = true" class="btn btn-blue" style="padding: 10px 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>📤</span> Evrak Yükle
        </button>
      </header>

      <!-- 5-Tab Navigation Bar -->
      <div class="category-tabs-bar">
        <button @click="selectTab('kullanicilar')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'kullanicilar' }">
          <span>👥</span> Kullanıcılar
        </button>
        <button @click="selectTab('teslim_formlari')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'teslim_formlari' }">
          <span>📋</span> Teslim Formları
        </button>
        <button @click="selectTab('bayi_sozlesmesi')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'bayi_sozlesmesi' }">
          <span>📜</span> Bayi Sözleşmesi
        </button>
        <button @click="selectTab('sirket_evraklari')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'sirket_evraklari' }">
          <span>🏢</span> Şirket Evraklarım
        </button>
        <button @click="selectTab('entegrasyonlar')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'entegrasyonlar' }">
          <span>📡</span> API & Entegrasyonlar
        </button>
      </div>


      <!-- ============================================================== -->
      <!-- 1. KULLANICILAR (Kullanıcı Listesi ve Kullanıcı Ekleme)       -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'kullanicilar'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a;">Sistem Kullanıcıları</h2>
            <div style="width: 280px;">
              <input type="text" v-model="userSearch" class="form-input" placeholder="Ad, e-posta veya rol ara...">
            </div>
          </div>

          <!-- User Table -->
          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Kullanıcı Adı / E-Posta</th>
                  <th>Telefon</th>
                  <th>Kullanıcı Rolü</th>
                  <th>Tahsis Edilen Araç</th>
                  <th>Kayıt Tarihi</th>
                  <th>Durum</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.id">
                  <td>#{{ user.id }}</td>
                  <td>
                    <strong style="color: #0f172a; font-size: 0.95rem;">{{ user.name }}</strong>
                    <div style="font-size: 0.8rem; color: #64748b;">{{ user.email }}</div>
                  </td>
                  <td>{{ user.phone }}</td>
                  <td>
                    <span class="badge" :class="getRoleBadgeClass(user.role)">{{ user.role }}</span>
                  </td>
                  <td>
                    <span v-if="user.assigned_plate" style="font-family: monospace; font-weight: 700; color: #2563eb; background: #eff6ff; padding: 4px 10px; border-radius: 6px; border: 1px solid #bfdbfe;">
                      {{ user.assigned_plate }}
                    </span>
                    <span v-else style="color: #94a3b8; font-size: 0.85rem;">— Tahsis Yok</span>
                  </td>
                  <td>{{ user.created_at }}</td>
                  <td>
                    <span style="font-size: 0.8rem; font-weight: 700; padding: 4px 10px; border-radius: 20px;"
                      :style="{ background: user.is_active ? '#dcfce7' : '#fef2f2', color: user.is_active ? '#16a34a' : '#dc2626' }">
                      {{ user.is_active ? '🟢 Aktif' : '🔴 Pasif' }}
                    </span>
                  </td>
                  <td>
                    <div style="display: flex; gap: 8px;">
                      <button @click="editUser(user)" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.78rem;">
                        Düzenle
                      </button>
                      <button @click="toggleUserStatus(user)" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.78rem;" :style="{ color: user.is_active ? '#dc2626' : '#16a34a' }">
                        {{ user.is_active ? 'Pasife Al' : 'Aktif Et' }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Summary Stat Cards -->
        <div class="grid-3" style="gap: 20px;">
          <div class="glass-panel text-center" style="padding: 20px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 16px;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #2563eb;">{{ users.length }} Kullanıcı</div>
            <div style="font-size: 0.85rem; color: #1d4ed8; margin-top: 4px;">Toplam Kayıtlı Kullanıcı</div>
          </div>
          <div class="glass-panel text-center" style="padding: 20px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 16px;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #16a34a;">{{ activeUsersCount }} Aktif</div>
            <div style="font-size: 0.85rem; color: #15803d; margin-top: 4px;">Sistemi Kullanan Yetkililer</div>
          </div>
          <div class="glass-panel text-center" style="padding: 20px; background: #fefce8; border: 1px solid #fef08a; border-radius: 16px;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #d97706;">{{ driverUsersCount }} Sürücü</div>
            <div style="font-size: 0.85rem; color: #b45309; margin-top: 4px;">Araç Zimmetli Sürücüler</div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 2. TESLİM FORMLARI                                             -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'teslim_formlari'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Araç Teslim & Tesellüm Formları</h2>

          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Form No</th>
                  <th>Plaka</th>
                  <th>Teslim Alan Kullanıcı</th>
                  <th>Teslim Eden Yetkili</th>
                  <th>Teslim Tarihi</th>
                  <th>Başlangıç KM</th>
                  <th>Araç Hasar / Not</th>
                  <th>Doküman</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="form in deliveryForms" :key="form.id">
                  <td><strong style="color: #2563eb;">#TF-{{ form.id }}</strong></td>
                  <td><strong style="color: #0f172a;">{{ form.plate }}</strong></td>
                  <td>{{ form.receiver }}</td>
                  <td>{{ form.issuer }}</td>
                  <td>{{ form.date }}</td>
                  <td>{{ form.km.toLocaleString() }} km</td>
                  <td><span style="font-size: 0.85rem; color: #64748b;">{{ form.notes }}</span></td>
                  <td>
                    <button @click="downloadForm(form)" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.78rem; color: #2563eb;">
                      📄 İmzalı Form (PDF)
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 3. BAYİ SÖZLEŞMESİ                                              -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'bayi_sozlesmesi'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Aktif Bayi ve Tedarikçi Sözleşmeleri</h2>

          <div class="grid-2" style="gap: 20px;">
            <div class="glass-panel" style="padding: 20px; background: #fafafa; border: 1px solid #e2e8f0; border-radius: 14px;" v-for="contract in contracts" :key="contract.id">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div>
                  <h3 style="font-size: 1.1rem; font-weight: 800; color: #0f172a;">{{ contract.name }}</h3>
                  <div style="font-size: 0.85rem; color: #64748b;">Sözleşme No: <strong>#BS-{{ contract.code }}</strong></div>
                </div>
                <span class="badge badge-active">Yürürlükte</span>
              </div>

              <div style="font-size: 0.88rem; color: #475569; margin-bottom: 15px; line-height: 1.6;">
                <div><strong>Başlangıç Tarihi:</strong> {{ contract.start_date }}</div>
                <div><strong>Bitiş Tarihi:</strong> {{ contract.end_date }}</div>
                <div><strong>Komisyon / Hizmet Oranı:</strong> {{ contract.commission }}</div>
              </div>

              <button @click="downloadContract(contract)" class="btn btn-secondary" style="width: 100%; font-size: 0.85rem; font-weight: 600; color: #2563eb;">
                📄 İmzalı Bayi Sözleşmesini İndir (PDF)
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 4. ŞİRKET EVRAKLARIM                                            -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'sirket_evraklari'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
              <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a;">Kurumsal Şirket Evrakları & Belgeler</h2>
              <p style="font-size: 0.88rem; color: #64748b; margin-top: 4px;">Kiralama teklifleri ve sözleşmeler için yüklediğiniz şirket evraklarını buradan yönetin.</p>
            </div>
            <button @click="openUploadModal(null)" class="btn btn-blue" style="padding: 10px 18px; font-weight: 700; font-size: 0.88rem; display: flex; align-items: center; gap: 8px;">
              <span>📤</span> Yeni Evrak Yükle
            </button>
          </div>

          <div class="grid-2" style="gap: 20px;">
            <div class="glass-panel" style="padding: 20px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; display: flex; flex-direction: column; justify-content: space-between;" v-for="cat in docCategories" :key="cat.key">
              <div>
                <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 12px;">
                  <div style="width: 44px; height: 44px; border-radius: 10px; background: #eff6ff; color: #2563eb; font-size: 1.4rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    {{ cat.icon }}
                  </div>
                  <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                      <h4 style="font-size: 1rem; font-weight: 800; color: #0f172a; margin: 0;">{{ cat.title }}</h4>
                      <span v-if="customerDocs[cat.key]" class="badge badge-active">✓ {{ customerDocs[cat.key].status || 'Onaylandı' }}</span>
                      <span v-else style="background: #fef3c7; color: #b45309; font-size: 0.78rem; font-weight: 700; padding: 3px 10px; border-radius: 20px;">⚠️ Yüklenmedi</span>
                    </div>
                    <div v-if="customerDocs[cat.key]" style="font-size: 0.82rem; color: #475569; font-weight: 600; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                      📁 {{ customerDocs[cat.key].file_name }}
                    </div>
                    <div v-else style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                      {{ cat.required ? '*Zorunlu Belge' : 'Opsiyonel Belge' }}
                    </div>
                  </div>
                </div>

                <div v-if="customerDocs[cat.key]" style="font-size: 0.78rem; color: #64748b; margin-bottom: 15px;">
                  Yükleme Tarihi: {{ customerDocs[cat.key].uploaded_at }}
                </div>
              </div>

              <div style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                <template v-if="customerDocs[cat.key]">
                  <button @click="viewCustomerDoc(cat.key)" class="btn btn-secondary" style="flex: 1; min-width: 80px; font-size: 0.8rem; padding: 7px 10px;">
                    👁️ Görüntüle
                  </button>
                  <button @click="downloadCustomerDoc(cat.key)" class="btn btn-blue" style="flex: 1; min-width: 70px; font-size: 0.8rem; padding: 7px 10px;">
                    ⬇️ İndir
                  </button>
                  <button @click="openUploadModal(cat.key)" class="btn btn-secondary" style="font-size: 0.8rem; padding: 7px 10px;">
                    🔄 Yenile
                  </button>
                  <button @click="deleteCustomerDoc(cat.key)" class="btn btn-secondary" style="color: #dc2626; font-size: 0.8rem; padding: 7px 10px;">
                    🗑️ Sil
                  </button>
                </template>
                <template v-else>
                  <button @click="openUploadModal(cat.key)" class="btn btn-blue" style="width: 100%; font-size: 0.85rem; padding: 9px 12px; font-weight: 700;">
                    📤 Belge Yükle
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>


      <!-- ============================================================== -->
      <!-- 5. API & ENTEGRASYONLAR                                       -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'entegrasyonlar'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">GPS ve UTTS Canlı Veri Entegrasyon Yapılandırması</h2>
          <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 24px;">
            Araçlarınıza tanımladığınız GPS Cihaz ID ve UTTS Taşıt Tanıma kodlarının canlı veri akışını aktifleştirmek için servis sağlayıcı API erişim bilgilerinizi girin.
          </p>

          <div class="grid-2" style="gap: 24px;">
            <!-- GPS Provider API Config -->
            <div style="border: 1px solid #e2e8f0; border-radius: 14px; padding: 24px; background: #fafafa;">
              <h3 style="font-size: 1.1rem; font-weight: 800; color: #2563eb; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                <span>📡</span> GPS Araç Takip Entegrasyonu
              </h3>

              <form @submit.prevent="saveGpsSettings">
                <div class="form-group">
                  <label class="form-label">GPS Servis Sağlayıcısı</label>
                  <select v-model="gpsConfig.provider" class="form-select">
                    <option value="Arvento">Arvento Mobile Systems</option>
                    <option value="Mobiliz">Mobiliz Takip Sistemleri</option>
                    <option value="Trio">Trio Mobil</option>
                    <option value="FiloTurk">FiloTürk GPS</option>
                    <option value="Infotech">Infotech GPS</option>
                    <option value="GenericWebhook">Özel REST Webhook API</option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">API Kullanıcı Adı / Müşteri Kodu</label>
                  <input type="text" v-model="gpsConfig.apiKey" class="form-input" placeholder="Örn: FLEET-API-USER-99">
                </div>

                <div class="form-group">
                  <label class="form-label">API Gizli Anahtarı / Token</label>
                  <input type="password" v-model="gpsConfig.apiSecret" class="form-input" placeholder="••••••••••••••••">
                </div>

                <div class="form-group">
                  <label class="form-label">Veri Yenileme Sıklığı</label>
                  <select v-model="gpsConfig.interval" class="form-select">
                    <option value="15">Her 15 saniyede bir (Canlı Stream)</option>
                    <option value="60">Her 1 dakikada bir</option>
                    <option value="300">Her 5 dakikada bir</option>
                  </select>
                </div>

                <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 0.82rem; font-weight: 700; color: #16a34a;">🟢 GPS Servisi Bağlı</span>
                  <button type="submit" class="btn btn-blue" style="padding: 8px 16px; font-size: 0.85rem;">Ayarları Kaydet</button>
                </div>
              </form>
            </div>

            <!-- UTTS & Fuel Config -->
            <div style="border: 1px solid #e2e8f0; border-radius: 14px; padding: 24px; background: #fafafa;">
              <h3 style="font-size: 1.1rem; font-weight: 800; color: #059669; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                <span>⛽</span> UTTS Taşıt Tanıma Entegrasyonu
              </h3>

              <form @submit.prevent="saveUttsSettings">
                <div class="form-group">
                  <label class="form-label">UTTS / Akaryakıt Tedarikçisi</label>
                  <select v-model="uttsConfig.provider" class="form-select">
                    <option value="DarphaneUTTS">Darphane Ulusal Taşıt Tanıma Sistemi (UTTS API)</option>
                    <option value="Shell">Shell Taşıt Tanıma</option>
                    <option value="BP">BP FleetPass</option>
                    <option value="PetrolOfisi">Petrol Ofisi AutoMatic</option>
                    <option value="Opet">Opet Otobil</option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Kurumsal Müşteri / Cari Kodu</label>
                  <input type="text" v-model="uttsConfig.clientCode" class="form-input" placeholder="Örn: UTTS-COMPANY-4482">
                </div>

                <div class="form-group">
                  <label class="form-label">Otomatik Harcama Eşitleme</label>
                  <select v-model="uttsConfig.syncType" class="form-select">
                    <option value="Daily">Günlük Otomatik Fiş/Harcama Çekme</option>
                    <option value="Realtime">Anlık Yakıt Alımı Bildirimi</option>
                    <option value="Monthly">Aylık Fatura İçe Aktarımı</option>
                  </select>
                </div>

                <div style="margin-top: 60px; display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 0.82rem; font-weight: 700; color: #16a34a;">🟢 UTTS Servisi Aktif</span>
                  <button type="submit" class="btn btn-blue" style="padding: 8px 16px; font-size: 0.85rem;">Ayarları Kaydet</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- 👤 NEW USER MODAL (KULLANICI EKLEME EKRANI) -->
  <div v-if="showAddUserModal" class="modal-overlay" @click.self="showAddUserModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 540px; padding: 32px; background: #ffffff;">
      <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">Yeni Kullanıcı Ekle</h2>
      <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 24px;">
        Sisteme erişecek yeni yönetici, sürücü veya operasyon personelini tanımlayın.
      </p>

      <form @submit.prevent="addUser">
        <div class="form-group">
          <label class="form-label">Ad Soyad *</label>
          <input type="text" v-model="userForm.name" required class="form-input" placeholder="Örn: Caner Erkin">
        </div>

        <div class="grid-2" style="gap: 16px;">
          <div class="form-group">
            <label class="form-label">E-Posta Adresi *</label>
            <input type="email" v-model="userForm.email" required class="form-input" placeholder="isim@sirket.com">
          </div>

          <div class="form-group">
            <label class="form-label">Telefon Numarası *</label>
            <input type="tel" v-model="userForm.phone" required class="form-input" placeholder="0532 000 00 00">
          </div>
        </div>

        <div class="grid-2" style="gap: 16px;">
          <div class="form-group">
            <label class="form-label">Kullanıcı Rolü *</label>
            <select v-model="userForm.role" required class="form-select">
              <option value="Sürücü">Sürücü</option>
              <option value="Filo Yöneticisi">Filo Yöneticisi</option>
              <option value="Finans Sorumlusu">Finans Sorumlusu</option>
              <option value="Operasyon Personeli">Operasyon Personeli</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Tahsis Edilecek Araç</label>
            <select v-model="userForm.assigned_plate" class="form-select">
              <option value="">Yok / Serbest</option>
              <option v-for="v in vehicles" :key="v.id" :value="v.plate">
                {{ v.plate }} ({{ v.brand }} {{ v.model }})
              </option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Giriş Şifresi *</label>
          <input type="password" v-model="userForm.password" required class="form-input" placeholder="••••••••">
          <span style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Kullanıcı ilk girişte şifresini değiştirebilir</span>
        </div>

        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 25px;">
          <button type="button" @click="showAddUserModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-blue" style="padding: 12px 24px;">Kullanıcıyı Kaydet</button>
        </div>
      </form>
    </div>
  </div>

  <!-- 📋 NEW HANDOVER FORM MODAL -->
  <div v-if="showAddFormModal" class="modal-overlay" @click.self="showAddFormModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 500px; padding: 30px; background: #ffffff;">
      <h2 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Yeni Araç Teslim Formu</h2>
      <form @submit.prevent="addHandoverForm">
        <div class="form-group">
          <label class="form-label">Teslim Edilecek Araç Plakası</label>
          <select v-model="formHandover.plate" required class="form-select">
            <option value="" disabled>Araç seçiniz...</option>
            <option v-for="v in vehicles" :key="v.id" :value="v.plate">
              {{ v.plate }} ({{ v.brand }} {{ v.model }})
            </option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Teslim Alan Kullanıcı</label>
          <input type="text" v-model="formHandover.receiver" required class="form-input" placeholder="Ad Soyad">
        </div>
        <div class="form-group">
          <label class="form-label">Teslim Tarihi</label>
          <input type="date" v-model="formHandover.date" required class="form-input">
        </div>
        <div class="form-group">
          <label class="form-label">Mevcut Kilometre</label>
          <input type="number" v-model.number="formHandover.km" required class="form-input" placeholder="45230">
        </div>
        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px;">
          <button type="button" @click="showAddFormModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-blue">Formu Oluştur</button>
        </div>
      </form>
    </div>
  </div>

  <!-- 📤 UPLOAD DOCUMENT MODAL -->
  <div v-if="showUploadDocModal" class="modal-overlay" @click.self="showUploadDocModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 500px; padding: 30px; background: #ffffff;">
      <h2 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">Şirket Evrakı Yükle / Güncelle</h2>
      <p style="font-size: 0.85rem; color: #64748b; margin-bottom: 20px;">Lütfen yüklemek istediğiniz belge kategorisini seçin ve dosyanızı ekleyin.</p>
      
      <form @submit.prevent="saveCustomerDoc">
        <div class="form-group">
          <label class="form-label">Belge Kategorisi *</label>
          <select v-model="selectedDocCategory" required class="form-select">
            <option value="tax_plate">📄 Vergi Levhası</option>
            <option value="signature_circular">✒️ İmza Sirküleri</option>
            <option value="activity_certificate">🏛️ Oda Kayıt & Faaliyet Belgesi</option>
            <option value="trade_registry">📜 Ticaret Sicil Gazetesi</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Dosya Seçin *</label>
          <input type="file" @change="onDocFilePicked" accept=".pdf,.png,.jpg,.jpeg" required class="form-input" style="padding: 8px;">
          <span v-if="uploadFileName" style="font-size: 0.8rem; color: #16a34a; margin-top: 4px; display: block; font-weight: 600;">Seçilen: {{ uploadFileName }}</span>
        </div>

        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 25px;">
          <button type="button" @click="showUploadDocModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-blue" :disabled="docSubmitting">
            {{ docSubmitting ? 'Kaydediliyor...' : 'Yükle ve Kaydet' }}
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- 👁️ PREVIEW DOCUMENT MODAL -->
  <div v-if="showPreviewModal" class="modal-overlay" @click.self="showPreviewModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 550px; padding: 30px; background: #ffffff;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin: 0;">Belge Önizleme</h2>
        <button class="close-btn" @click="showPreviewModal = false">✕</button>
      </div>

      <div v-if="previewDocData" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px;">
        <div style="font-size: 3rem; margin-bottom: 10px;">📄</div>
        <h3 style="font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-bottom: 4px;">{{ previewDocData.title }}</h3>
        <div style="font-size: 0.85rem; color: #2563eb; font-weight: 700; margin-bottom: 8px;">Dosya: {{ previewDocData.file_name }}</div>
        <span class="badge badge-active" style="display: inline-block;">✓ Status: {{ previewDocData.status || 'Onaylandı' }}</span>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 10px;">Yükleme Tarihi: {{ previewDocData.uploaded_at }}</div>
      </div>

      <div style="display: flex; gap: 12px; justify-content: flex-end;">
        <button type="button" @click="showPreviewModal = false" class="btn btn-secondary">Kapat</button>
        <button type="button" @click="downloadCustomerDoc(previewDocData.key)" class="btn btn-blue">⬇️ Belgeyi İndir</button>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'

const route = useRoute()
const router = useRouter()
const activeTab = ref(route.query.tab || 'kullanicilar')

const selectTab = (tabKey) => {
  activeTab.value = tabKey
  router.replace({ query: { ...route.query, tab: tabKey } })
}

watch(() => route.query.tab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
})


const userSearch = ref('')
const showAddUserModal = ref(false)
const showAddFormModal = ref(false)
const showUploadDocModal = ref(false)
const newDocTitle = ref('')

const gpsConfig = reactive({
  provider: 'Arvento',
  apiKey: localStorage.getItem('gps_api_key') || '',
  apiSecret: localStorage.getItem('gps_api_secret') || '',
  interval: '15'
})

const uttsConfig = reactive({
  provider: 'DarphaneUTTS',
  clientCode: localStorage.getItem('utts_client_code') || '',
  syncType: 'Daily'
})

const saveGpsSettings = () => {
  localStorage.setItem('gps_provider', gpsConfig.provider)
  localStorage.setItem('gps_api_key', gpsConfig.apiKey)
  localStorage.setItem('gps_api_secret', gpsConfig.apiSecret)
  alert('GPS Servis Sağlayıcısı API ayarları kaydedildi!')
}

const saveUttsSettings = () => {
  localStorage.setItem('utts_provider', uttsConfig.provider)
  localStorage.setItem('utts_client_code', uttsConfig.clientCode)
  alert('UTTS Taşıt Tanıma entegrasyon ayarları kaydedildi!')
}

const activeTabTitle = computed(() => {
  switch (activeTab.value) {
    case 'kullanicilar': return 'Kullanıcılar'
    case 'teslim_formlari': return 'Teslim Formları'
    case 'bayi_sozlesmesi': return 'Bayi Sözleşmesi'
    case 'sirket_evraklari': return 'Şirket Evraklarım'
    case 'entegrasyonlar': return 'API & Entegrasyonlar'
    default: return 'Ayarlar'
  }
})

// Vehicles state for plate selects
const vehicles = ref([])

const fetchVehicles = async () => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  const url = customerId ? `/api/vehicles?customer_id=${customerId}` : '/api/vehicles'
  try {
    const res = await fetch(url)
    if (res.ok) {
      vehicles.value = await res.json()
    }
  } catch (err) {
    console.error('Error fetching vehicles for settings:', err)
  }
}

// Users List Data
const storedUsersStr = localStorage.getItem('fleet_customer_users')
const defaultUser = {
  id: 1,
  name: localStorage.getItem('fleetcar_customer_name') || 'Filo Yöneticisi',
  email: localStorage.getItem('fleetcar_user_email') || 'yonetici@sirket.com',
  phone: '-',
  role: 'Filo Yöneticisi',
  assigned_plate: '',
  created_at: new Date().toLocaleDateString('tr-TR'),
  is_active: true
}

const users = ref(storedUsersStr ? JSON.parse(storedUsersStr) : [defaultUser])

const saveUsers = () => {
  localStorage.setItem('fleet_customer_users', JSON.stringify(users.value))
}

const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  const q = userSearch.value.toLowerCase()
  return users.value.filter(u => 
    u.name.toLowerCase().includes(q) || 
    u.email.toLowerCase().includes(q) || 
    u.role.toLowerCase().includes(q)
  )
})

const activeUsersCount = computed(() => users.value.filter(u => u.is_active).length)
const driverUsersCount = computed(() => users.value.filter(u => u.role === 'Sürücü').length)

const userForm = reactive({
  name: '',
  email: '',
  phone: '',
  role: 'Sürücü',
  assigned_plate: '',
  password: '123456'
})

const addUser = () => {
  users.value.unshift({
    id: Date.now(),
    name: userForm.name,
    email: userForm.email,
    phone: userForm.phone,
    role: userForm.role,
    assigned_plate: userForm.assigned_plate,
    created_at: new Date().toLocaleDateString('tr-TR'),
    is_active: true
  })
  saveUsers()
  alert(`Yeni kullanıcı "${userForm.name}" başarıyla eklendi!`)
  showAddUserModal.value = false
  userForm.name = ''
  userForm.email = ''
  userForm.phone = ''
  userForm.assigned_plate = ''
}

const toggleUserStatus = (user) => {
  user.is_active = !user.is_active
  saveUsers()
}

const editUser = (user) => {
  alert(`"${user.name}" kullanıcısını düzenleme ekranı açılıyor...`)
}

// Delivery / Handover Forms
const storedFormsStr = localStorage.getItem('fleet_customer_delivery_forms')
const deliveryForms = ref(storedFormsStr ? JSON.parse(storedFormsStr) : [])

const saveForms = () => {
  localStorage.setItem('fleet_customer_delivery_forms', JSON.stringify(deliveryForms.value))
}

const formHandover = reactive({
  plate: '',
  receiver: '',
  date: new Date().toISOString().slice(0, 10),
  km: 0
})

const addHandoverForm = () => {
  deliveryForms.value.unshift({
    id: Date.now(),
    plate: formHandover.plate,
    receiver: formHandover.receiver,
    issuer: localStorage.getItem('fleetcar_customer_name') || 'Filo Yönetimi',
    date: formHandover.date,
    km: formHandover.km,
    notes: 'Yeni teslim alma formu kaydı.'
  })
  saveForms()
  showAddFormModal.value = false
  alert(`${formHandover.plate} plaka için araç teslim formu kaydedildi!`)
}

// Company Docs Data & Methods
const customerDocs = ref({})
const documentsUploaded = ref(false)

const docCategories = [
  { key: 'tax_plate', title: 'Vergi Levhası', icon: '📄', required: true },
  { key: 'signature_circular', title: 'İmza Sirküleri', icon: '✒️', required: true },
  { key: 'activity_certificate', title: 'Oda Kayıt & Faaliyet Belgesi', icon: '🏛️', required: true },
  { key: 'trade_registry', title: 'Ticaret Sicil Gazetesi', icon: '📜', required: true }
]

const selectedDocCategory = ref('tax_plate')
const uploadFileName = ref('')
const docSubmitting = ref(false)
const showPreviewModal = ref(false)
const previewDocData = ref(null)

const fetchCustomerDocs = async () => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  if (!customerId) return
  try {
    const res = await fetch(`/api/customer/documents?customer_id=${customerId}`)
    if (res.ok) {
      const data = await res.json()
      customerDocs.value = data.documents || {}
      documentsUploaded.value = Boolean(data.documents_uploaded)
    }
  } catch (err) {
    console.error('Error fetching customer docs:', err)
  }
}

const openUploadModal = (key = null) => {
  if (key) {
    selectedDocCategory.value = key
  } else {
    selectedDocCategory.value = 'tax_plate'
  }
  uploadFileName.value = ''
  showUploadDocModal.value = true
}

const onDocFilePicked = (event) => {
  const file = event.target.files[0]
  if (file) {
    uploadFileName.value = file.name
  }
}

const saveCustomerDoc = async () => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  if (!customerId) {
    alert('Müşteri oturumu bulunamadı. Lütfen tekrar giriş yapın.')
    return
  }

  docSubmitting.value = true
  const payload = {
    customer_id: Number(customerId)
  }
  payload[selectedDocCategory.value] = uploadFileName.value || `${selectedDocCategory.value}_belge.pdf`

  try {
    const res = await fetch('/api/customer/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (res.ok) {
      const data = await res.json()
      customerDocs.value = data.customer?.documents || {}
      documentsUploaded.value = Boolean(data.customer?.documents_uploaded)
      showUploadDocModal.value = false
      alert('Şirket evrakı başarıyla yüklendi!')
    } else {
      alert('Evrak yüklenirken bir sorun oluştu.')
    }
  } catch (err) {
    console.error('Error saving customer doc:', err)
    alert('Sunucuya bağlanılamadı.')
  } finally {
    docSubmitting.value = false
  }
}

const deleteCustomerDoc = async (key) => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  if (!customerId) return

  const catObj = docCategories.find(c => c.key === key)
  const title = catObj ? catObj.title : key

  if (!confirm(`"${title}" evrakını silmek istediğinize emin misiniz?`)) return

  try {
    const res = await fetch(`/api/customer/documents/${key}?customer_id=${customerId}`, {
      method: 'DELETE'
    })

    if (res.ok) {
      const data = await res.json()
      customerDocs.value = data.customer?.documents || {}
      documentsUploaded.value = Boolean(data.customer?.documents_uploaded)
      alert(`"${title}" belgesi başarıyla silindi.`)
    } else {
      alert('Belge silinirken bir sorun oluştu.')
    }
  } catch (err) {
    console.error('Error deleting doc:', err)
    alert('Sunucuya bağlanılamadı.')
  }
}

const viewCustomerDoc = (key) => {
  const doc = customerDocs.value[key]
  const catObj = docCategories.find(c => c.key === key)
  if (doc) {
    previewDocData.value = {
      key,
      title: catObj ? catObj.title : key,
      file_name: doc.file_name,
      uploaded_at: doc.uploaded_at,
      status: doc.status
    }
    showPreviewModal.value = true
  }
}

const downloadCustomerDoc = (key) => {
  const doc = customerDocs.value[key]
  const catObj = docCategories.find(c => c.key === key)
  const filename = doc?.file_name || `${key}_belge.pdf`
  
  const content = `FleetCar Kurumsal Şirket Evrakı\nBelge Türü: ${catObj?.title || key}\nDosya Adı: ${filename}\nYüklenme Tarihi: ${doc?.uploaded_at || 'Bilinmiyor'}\nDurum: Onaylı`
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

onMounted(() => {
  fetchVehicles()
  fetchCustomerDocs()
})

const getRoleBadgeClass = (role) => {
  switch (role) {
    case 'Filo Yöneticisi': return 'badge-service'
    case 'Finans Sorumlusu': return 'badge-tire'
    case 'Operasyon Personeli': return 'badge-replacement'
    default: return 'badge-active'
  }
}
</script>

