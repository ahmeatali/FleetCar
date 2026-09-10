<template>
  <div>
    <!-- Navbar -->
    <nav class="navbar" style="padding: 16px 8%; background: #ffffff; border-bottom: 1px solid #e2e8f0;">
      <router-link to="/" class="nav-logo">
        <div class="nav-logo-icon" style="background: #2563eb; border-radius: 8px;">⇄</div>
        <span style="font-weight: 800; font-size: 1.4rem; color: #0f172a;">FleetRent</span>
      </router-link>
      
      <ul class="nav-links">
        <li><a href="#vehicles" class="nav-link" style="color: #475569;">Araçlar <span style="font-size: 0.75rem;">▼</span></a></li>
        <li><a href="#compare" class="nav-link" style="color: #475569;">Karşılaştır</a></li>
        <li><a href="#ai-assistant" class="nav-link" style="color: #475569; font-weight: 600;">✨ AI Asistan</a></li>
        <li><a href="#partners" class="nav-link" style="color: #475569;">Kurumsal</a></li>
        <li><a href="#contact" class="nav-link" style="color: #475569;">İletişim</a></li>
      </ul>

      <div style="display: flex; align-items: center; gap: 16px;">
        <div class="fleetrent-nav-search">
          <span style="color: #94a3b8;">🔍</span>
          <input type="text" placeholder="Ara..." v-model="searchQuery" @keyup.enter="handleSearch" />
        </div>
        <button @click="showLoginRoleModal = true" class="nav-link" style="background: none; border: none; cursor: pointer; color: #334155; font-weight: 600; font-size: 0.95rem;">
          Giriş
        </button>
      </div>
    </nav>

    <!-- HERO SECTION (Dark Theme Grid Background) -->
    <section class="hero-dark-bg">
      <div class="container" style="max-width: 900px; padding: 0;">
        <div class="hero-pill-badge">
          <span>✨</span>
          <span>Yapay Zeka Destekli Araç Kiralama Platformu</span>
        </div>

        <h1 class="hero-dark-title" style="color: #ffffff;">
          Uzun Dönem Araç
          <span class="cyan-text">Kiralamada Fark</span>
        </h1>

        <p class="hero-dark-subtitle">
          150+ tedarikçiyi anında karşılaştırın. AI asistanımız size en uygun aracı ve en iyi fiyatı bulsun. Ücretsiz, hızlı, güvenilir.
        </p>

        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
          <button @click="openQuoteModal('kurumsal')" class="btn btn-blue" style="padding: 14px 28px; font-size: 1rem;">
            Kurumsal Teklif Al
          </button>
          <button @click="openQuoteModal('bireysel')" class="btn" style="background: #ffffff; color: #0f172a; font-weight: 600; padding: 14px 28px; font-size: 1rem; border-radius: 8px;">
            Bireysel Teklif Al
          </button>
          <button @click="openQuoteModal('r2r')" class="btn btn-dark-outline" style="padding: 14px 28px; font-size: 1rem; border-radius: 8px;">
            R2R Teklif Al
          </button>
        </div>

        <!-- Trust Badges Row -->
        <div class="trust-badges-row">
          <div class="trust-badge-item">
            <span>🛡️</span>
            <span>SSL Güvenli Ödeme</span>
          </div>
          <div class="trust-badge-item">
            <span>🕒</span>
            <span>7/24 Müşteri Desteği</span>
          </div>
          <div class="trust-badge-item">
            <span>📉</span>
            <span>En İyi Fiyat Garantisi</span>
          </div>
          <div class="trust-badge-item">
            <span>👥</span>
            <span>150+ Tedarikçi</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 2: İŞ ORTAKLARIMIZ -->
    <section id="partners" class="container" style="padding: 80px 20px;">
      <div class="text-center" style="margin-bottom: 48px;">
        <span style="font-size: 0.8rem; font-weight: 700; color: #2563eb; letter-spacing: 0.12em; text-transform: uppercase;">GÜVENİLİR AĞIMIZ</span>
        <h2 style="font-size: 2.4rem; font-weight: 800; color: #0f172a; margin: 8px 0 12px;">İş Ortaklarımız</h2>
        <p style="color: #64748b; font-size: 1.05rem;">Türkiye'nin önde gelen otomotiv ve kiralama markaları ile güçlü iş birliği içindeyiz.</p>
      </div>

      <div class="grid-4" style="gap: 20px;">
        <!-- Partner 1 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #fee2e2; color: #dc2626;">TT</div>
          <div class="partner-info">
            <h4>Toyota Türkiye</h4>
            <p>Otomobil</p>
          </div>
        </div>

        <!-- Partner 2 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #dbeafe; color: #2563eb;">VW</div>
          <div class="partner-info">
            <h4>Volkswagen</h4>
            <p>Otomobil</p>
          </div>
        </div>

        <!-- Partner 3 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #f3e8ff; color: #7c3aed;">MB</div>
          <div class="partner-info">
            <h4>Mercedes-Benz</h4>
            <p>Premium</p>
          </div>
        </div>

        <!-- Partner 4 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #e0e7ff; color: #4338ca;">FD</div>
          <div class="partner-info">
            <h4>Ford Türkiye</h4>
            <p>Ticari & Otomobil</p>
          </div>
        </div>

        <!-- Partner 5 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #e0f2fe; color: #0284c7;">HY</div>
          <div class="partner-info">
            <h4>Hyundai</h4>
            <p>Otomobil</p>
          </div>
        </div>

        <!-- Partner 6 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #f1f5f9; color: #334155;">BM</div>
          <div class="partner-info">
            <h4>BMW Group</h4>
            <p>Premium</p>
          </div>
        </div>

        <!-- Partner 7 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #fef9c3; color: #ca8a04;">RN</div>
          <div class="partner-info">
            <h4>Renault Türkiye</h4>
            <p>Otomobil</p>
          </div>
        </div>

        <!-- Partner 8 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #ffedd5; color: #ea580c;">AB</div>
          <div class="partner-info">
            <h4>Avis Budget</h4>
            <p>Kiralama</p>
          </div>
        </div>

        <!-- Partner 9 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #fef3c7; color: #d97706;">HZ</div>
          <div class="partner-info">
            <h4>Hertz Türkiye</h4>
            <p>Kiralama</p>
          </div>
        </div>

        <!-- Partner 10 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #dcfce7; color: #16a34a;">GR</div>
          <div class="partner-info">
            <h4>Garenta</h4>
            <p>Kiralama</p>
          </div>
        </div>

        <!-- Partner 11 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #ccfbf1; color: #0d9488;">OT</div>
          <div class="partner-info">
            <h4>Otokoç Otomotiv</h4>
            <p>Filo</p>
          </div>
        </div>

        <!-- Partner 12 -->
        <div class="partner-card">
          <div class="partner-badge" style="background: #e0f2fe; color: #0284c7;">VF</div>
          <div class="partner-info">
            <h4>Vdf Filo</h4>
            <p>Filo</p>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 3: FARK YARATAN ÖZELLİKLER -->
    <section class="container" style="padding: 80px 20px;">
      <div class="text-center" style="margin-bottom: 48px;">
        <span style="font-size: 0.8rem; font-weight: 700; color: #2563eb; letter-spacing: 0.12em; text-transform: uppercase;">NEDEN FLEETRENT?</span>
        <h2 style="font-size: 2.4rem; font-weight: 800; color: #0f172a; margin: 8px 0 0;">Fark Yaratan Özellikler</h2>
      </div>

      <div class="grid-3" style="gap: 24px;">
        <!-- Feature 1 -->
        <div class="feature-box">
          <div class="feature-icon-square">⚡</div>
          <h3>Hızlı Teklif</h3>
          <p>Yapay zeka destekli sistemimiz sayesinde dakikalar içinde rekabetçi filo kiralama tekliflerinizi hazırlayın.</p>
        </div>

        <!-- Feature 2 -->
        <div class="feature-box">
          <div class="feature-icon-square">🛡️</div>
          <h3>Tam Kapsamlı Sigorta</h3>
          <p>Kasko ve trafik sigortası dahil paketlerimizle aracınızı her koşulda güvence altına alın.</p>
        </div>

        <!-- Feature 3 -->
        <div class="feature-box">
          <div class="feature-icon-square">🔧</div>
          <h3>Bakım & Servis</h3>
          <p>Periyodik bakım, lastik değişimi ve kaza anlarında dakikalar içerisinde destek hizmeti.</p>
        </div>

        <!-- Feature 4 -->
        <div class="feature-box">
          <div class="feature-icon-square">🕒</div>
          <h3>7/24 Destek</h3>
          <p>Yapay zeka destekli sistemimiz sayesinde saniyeler içerisinde yol yardım ekibimiz hizmetinizde.</p>
        </div>

        <!-- Feature 5 -->
        <div class="feature-box">
          <div class="feature-icon-square">💍</div>
          <h3>Esnek Sözleşme</h3>
          <p>12 ila 48 ay arasında değişen kiralama süreleri ile bütçenize ve ihtiyacınıza göre plan seçin.</p>
        </div>

        <!-- Feature 6 -->
        <div class="feature-box">
          <div class="feature-icon-square">🏷️</div>
          <h3>Kurumsal İndirimler</h3>
          <p>Çoklu araç kiralamalarında özel kurumsal fiyatlar ve filo yönetimi avantajlarından yararlanın.</p>
        </div>
      </div>
    </section>

    <!-- SECTION 4: NASIL ÇALIŞIR? (Dark Section) -->
    <section class="process-dark-section">
      <div class="container" style="max-width: 1100px;">
        <div class="text-center" style="margin-bottom: 54px;">
          <span style="font-size: 0.8rem; font-weight: 700; color: #38bdf8; letter-spacing: 0.12em; text-transform: uppercase;">SÜREÇ</span>
          <h2 style="font-size: 2.4rem; font-weight: 800; color: #ffffff; margin: 8px 0 12px;">Nasıl Çalışır?</h2>
          <p style="color: #94a3b8; font-size: 1.05rem;">Dört basit adımda filo kiralama teklifinizi alın.</p>
        </div>

        <div class="grid-4" style="gap: 30px;">
          <!-- Step 1 -->
          <div class="process-step-item">
            <div class="step-number-circle">1</div>
            <h4>Teklif Türünü Seçin</h4>
            <p>Kurumsal, bireysel veya R2R ihtiyacınıza göre ilgili teklif formunu açın.</p>
          </div>

          <!-- Step 2 -->
          <div class="process-step-item">
            <div class="step-number-circle">2</div>
            <h4>Formu Doldurun</h4>
            <p>Araç tercihinizi, km limitinizi, kiralama sürenizi ve belgeleri yükleyin.</p>
          </div>

          <!-- Step 3 -->
          <div class="process-step-item">
            <div class="step-number-circle">3</div>
            <h4>Teklif Alın</h4>
            <p>Uzman ekibimiz en kısa sürede size özel fiyat teklifinizi hazırlayıp iletir.</p>
          </div>

          <!-- Step 4 -->
          <div class="process-step-item">
            <div class="step-number-circle">4</div>
            <h4>Sözleşmeyi İmzalayın</h4>
            <p>Teklifi onaylayın, sözleşmeyi imzalayın ve aracınızı teslim alın.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 5: MÜŞTERİLERİMİZ NE DİYOR? -->
    <section class="container" style="padding: 80px 20px;">
      <div class="text-center" style="margin-bottom: 48px;">
        <span style="font-size: 0.8rem; font-weight: 700; color: #2563eb; letter-spacing: 0.12em; text-transform: uppercase;">REFERANSLAR</span>
        <h2 style="font-size: 2.4rem; font-weight: 800; color: #0f172a; margin: 8px 0 0;">Müşterilerimiz Ne Diyor?</h2>
      </div>

      <div class="grid-3" style="gap: 24px;">
        <!-- Testimonial 1 -->
        <div class="testimonial-card">
          <div>
            <div class="testimonial-stars">⭐⭐⭐⭐⭐</div>
            <p class="testimonial-text">
              "FleetRent sayesinde 50 araçlık filomuzun kiralama sürecini çok daha hızlı ve verimli yönetiyoruz. Fiyatlar rekabetçi, destek ekibi çok ilgili."
            </p>
          </div>
          <div class="testimonial-author" style="border-top: 1px solid #f1f5f9; padding-top: 16px;">
            <h5>Ahmet Kaya</h5>
            <p>Satın Alma Müdürü, LogiTech A.Ş.</p>
          </div>
        </div>

        <!-- Testimonial 2 -->
        <div class="testimonial-card">
          <div>
            <div class="testimonial-stars">⭐⭐⭐⭐⭐</div>
            <p class="testimonial-text">
              "Bireysel uzun dönem kiralama için araştırırken FleetRent'i buldum. Formları doldurmak çok kolay ve kısa sürede dönüş sağlandı. Kesinlikle tavsiye ederim."
            </p>
          </div>
          <div class="testimonial-author" style="border-top: 1px solid #f1f5f9; padding-top: 16px;">
            <h5>Zeynep Arslan</h5>
            <p>Bireysel Kullanıcı</p>
          </div>
        </div>

        <!-- Testimonial 3 -->
        <div class="testimonial-card">
          <div>
            <div class="testimonial-stars">⭐⭐⭐⭐⭐</div>
            <p class="testimonial-text">
              "R2R portföyümüzü FleetRent üzerinden yönetmek inanılmaz kolaylaştı. Profesyonel bir ekip, her aşamada yanınızda."
            </p>
          </div>
          <div class="testimonial-author" style="border-top: 1px solid #f1f5f9; padding-top: 16px;">
            <h5>Murat Demir</h5>
            <p>Filo Direktörü, Ekspres Lojistik</p>
          </div>
        </div>
      </div>
    </section>

    <!-- FOOTER (Dark Theme) -->
    <footer id="contact" class="dark-footer">
      <div class="container" style="max-width: 1200px;">
        <div class="grid-4" style="gap: 40px; margin-bottom: 50px;">
          <!-- Col 1: Logo & About -->
          <div>
            <div class="nav-logo" style="margin-bottom: 16px;">
              <div class="nav-logo-icon" style="background: #2563eb; border-radius: 8px;">⇄</div>
              <span style="font-weight: 800; font-size: 1.4rem; color: #ffffff;">FleetRent</span>
            </div>
            <p style="font-size: 0.88rem; line-height: 1.6; color: #94a3b8; margin-bottom: 20px;">
              Türkiye'nin lider uzun dönem araç kiralama platformu. Kurumsal, bireysel ve R2R ihtiyaçlarınız için profesyonel çözümler sunuyoruz.
            </p>
            <div style="display: flex; gap: 12px;">
              <a href="#" style="width: 34px; height: 34px; background: rgba(255,255,255,0.06); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ffffff; text-decoration: none;">f</a>
              <a href="#" style="width: 34px; height: 34px; background: rgba(255,255,255,0.06); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ffffff; text-decoration: none;">in</a>
              <a href="#" style="width: 34px; height: 34px; background: rgba(255,255,255,0.06); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ffffff; text-decoration: none;">ig</a>
              <a href="#" style="width: 34px; height: 34px; background: rgba(255,255,255,0.06); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ffffff; text-decoration: none;">yt</a>
            </div>
          </div>

          <!-- Col 2: Araçlar -->
          <div>
            <h4>ARAÇLAR</h4>
            <ul>
              <li><a href="#">Ekonomik</a></li>
              <li><a href="#">SUV & Crossover</a></li>
              <li><a href="#">Lüks</a></li>
              <li><a href="#">Elektrikli</a></li>
              <li><a href="#">Ticari</a></li>
            </ul>
          </div>

          <!-- Col 3: Hizmetler -->
          <div>
            <h4>HİZMETLER</h4>
            <ul>
              <li><a href="#" @click.prevent="openQuoteModal('bireysel')">Bireysel Kiralama</a></li>
              <li><a href="#" @click.prevent="openQuoteModal('kurumsal')">Kurumsal Kiralama</a></li>
              <li><a href="#" @click.prevent="openQuoteModal('r2r')">R2R Kiralama</a></li>
              <li><a href="#">Filo Yönetimi</a></li>
              <li><a href="#">AI Araç Önerisi</a></li>
            </ul>
          </div>

          <!-- Col 4: İletişim -->
          <div>
            <h4>İLETİŞİM</h4>
            <div class="footer-contact-item">
              <span>📞</span>
              <span>0850 532 12 34</span>
            </div>
            <div class="footer-contact-item">
              <span>✉️</span>
              <span>info@fleetrent.com.tr</span>
            </div>
            <div class="footer-contact-item">
              <span>✉️</span>
              <span>destek@fleetrent.com.tr</span>
            </div>
            <div class="footer-contact-item" style="align-items: flex-start;">
              <span style="margin-top: 2px;">📍</span>
              <span style="line-height: 1.4;">Maslak Mah. Büyükdere Cad. No: 255 Sarıyer / İstanbul</span>
            </div>
          </div>
        </div>

        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 25px; text-align: center; font-size: 0.82rem; color: #64748b;">
          © 2026 FleetRent Teknolojileri A.Ş. Tüm Hakları Saklıdır.
        </div>
      </div>
    </footer>

    <!-- Interactive Dynamic Multi-Step Quote Modal -->
    <div v-if="showQuoteModal" class="modal-overlay" @click.self="showQuoteModal = false">
      <div class="modal-card fade-in-up" style="max-width: 650px;">
        <!-- Modal Header -->
        <div class="modal-header" style="flex-direction: column; align-items: stretch; gap: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 class="modal-title" style="font-size: 1.3rem;">
              {{ selectedTypeTitle }} Kiralama Teklifi Al
            </h3>
            <button class="close-btn" @click="showQuoteModal = false">✕</button>
          </div>
          <p style="color: #64748b; font-size: 0.88rem; margin: 0;">
            Şirketiniz adına detaylı teklif talebi oluşturmak ve evraklarınızı iletmek için giriş yapın veya hızlıca kaydolun.
          </p>
        </div>

        <!-- AUTHENTICATION (Kayıt Ol / Giriş Yap) -->
        <div style="margin-top: 15px;">
          <div style="display: flex; gap: 10px; background: #f1f5f9; padding: 4px; border-radius: 12px; margin-bottom: 20px;">
            <button @click="authMode = 'register'" :style="{ background: authMode === 'register' ? '#ffffff' : 'transparent', color: authMode === 'register' ? '#0f172a' : '#64748b', fontWeight: authMode === 'register' ? '700' : '500' }" style="flex: 1; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.95rem;">
              🔑 Kayıt Ol (Yeni Hesap)
            </button>
            <button @click="authMode = 'login'" :style="{ background: authMode === 'login' ? '#ffffff' : 'transparent', color: authMode === 'login' ? '#0f172a' : '#64748b', fontWeight: authMode === 'login' ? '700' : '500' }" style="flex: 1; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.95rem;">
              👤 Giriş Yap
            </button>
          </div>

          <!-- Register Form -->
          <form v-if="authMode === 'register'" @submit.prevent="handleModalRegister">
            <p style="color: #64748b; font-size: 0.88rem; margin-bottom: 16px;">
              Teklif alma sürecine başlamak için lütfen öncelikle e-posta ve şifreniz ile kaydolun.
            </p>

            <div class="form-group">
              <label class="form-label">Şirket / Firma Adı *</label>
              <input type="text" v-model="form.company_name" required class="form-input" placeholder="Örn: Tekno Lojistik A.Ş.">
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
              <div class="form-group">
                <label class="form-label">E-posta Adresi *</label>
                <input type="email" v-model="form.email" required class="form-input" placeholder="isim@sirket.com">
              </div>
              <div class="form-group">
                <label class="form-label">Telefon Numarası *</label>
                <input type="tel" v-model="form.phone" required class="form-input" placeholder="05XX XXX XX XX">
              </div>
            </div>

            <div class="form-group" style="margin-bottom: 25px;">
              <label class="form-label">Şifre * (En az 6 karakter)</label>
              <input type="password" v-model="authPassword" required minlength="6" class="form-input" placeholder="••••••••">
            </div>

            <button type="submit" class="btn btn-blue" style="width: 100%; padding: 14px;" :disabled="submitting">
              {{ submitting ? 'Kaydolunuyor...' : 'Kaydol ve Şirket Evraklarına Geç ➔' }}
            </button>
          </form>

          <!-- Login Form -->
          <form v-else @submit.prevent="handleModalLogin">
            <p style="color: #64748b; font-size: 0.88rem; margin-bottom: 16px;">
              Mevcut müşteri hesabınızla giriş yaparak teklif sürecine devam edebilirsiniz.
            </p>

            <div class="form-group">
              <label class="form-label">E-posta Adresi *</label>
              <input type="email" v-model="form.email" required class="form-input" placeholder="isim@sirket.com">
            </div>

            <div class="form-group" style="margin-bottom: 25px;">
              <label class="form-label">Şifre *</label>
              <input type="password" v-model="authPassword" required class="form-input" placeholder="••••••••">
            </div>

            <button type="submit" class="btn btn-blue" style="width: 100%; padding: 14px;" :disabled="submitting">
              {{ submitting ? 'Giriş Yapılıyor...' : 'Giriş Yap ve Devam Et ➔' }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Login Role Selection Modal -->
    <div v-if="showLoginRoleModal" class="modal-overlay" @click.self="showLoginRoleModal = false">
      <div class="login-selection-card fade-in-up">
        <button class="close-btn" style="position: absolute; right: 20px; top: 20px;" @click="showLoginRoleModal = false">✕</button>
        
        <div class="nav-logo" style="justify-content: center; margin-bottom: 12px;">
          <div class="nav-logo-icon" style="background: #2563eb; border-radius: 8px;">⇄</div>
          <span style="font-weight: 800; font-size: 1.5rem; color: #0f172a;">FleetRent</span>
        </div>
        <p style="color: #64748b; font-size: 0.9rem; font-weight: 500;">Giriş tipini seçin</p>

        <div class="login-role-grid">
          <!-- 1. Müşteri Girişi -->
          <router-link to="/login?role=customer" class="login-role-tile tile-customer">
            <span class="tile-icon">🏢</span>
            <span class="tile-title">Müşteri Girişi</span>
            <span style="font-size: 0.75rem; color: #64748b; margin-top: 4px; font-weight: 500;">Filo Yönetim Paneli</span>
          </router-link>

          <!-- 2. Tedarikçi Girişi (Araba Sağlayıcı Kiralama Firmaları) -->
          <router-link to="/supplier-login" class="login-role-tile tile-supplier">
            <span class="tile-icon">🏭</span>
            <span class="tile-title">Tedarikçi Girişi</span>
            <span style="font-size: 0.75rem; color: #10b981; margin-top: 4px; font-weight: 600;">Araba Sağlayıcı & Kiralama</span>
          </router-link>

          <!-- 3. Servis Girişi (Bakım, Lastik & Oto Kurtarma) -->
          <router-link to="/service-login" class="login-role-tile tile-service">
            <span class="tile-icon">🔧</span>
            <span class="tile-title">Servis Girişi</span>
            <span style="font-size: 0.75rem; color: #2563eb; margin-top: 4px; font-weight: 600;">Bakım, Lastik & Oto Kurtarma</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="modal-overlay">
      <div class="modal-card fade-in-up" style="max-width: 500px; text-align: center; padding: 40px;">
        <div style="font-size: 3.5rem;">🎉</div>
        <h2 style="font-size: 1.8rem; font-weight: 800; color: #0f172a; margin: 15px 0 10px;">Teklifiniz Başarıyla Alındı!</h2>
        <p style="color: #64748b; margin-bottom: 20px; font-size: 0.95rem; line-height: 1.6;">
          <b>{{ submittedQuoteDetails?.company_name }}</b> adına aylık <b>₺{{ submittedQuoteDetails?.monthly_price_try?.toLocaleString() }}</b> tutarında teklif kaydı oluşturuldu.
        </p>
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 15px; border-radius: 10px; margin-bottom: 25px;">
          <p style="font-size: 0.85rem; color: #1e40af;">
            🔑 E-posta adresiniz ile yönetim portalına hemen giriş yapabilirsiniz.
          </p>
        </div>
        <div style="display: flex; gap: 12px; justify-content: center;">
          <button @click="goToLogin" class="btn btn-blue">Yönetim Paneline Git</button>
          <button @click="showSuccessModal = false" class="btn btn-secondary">Kapat</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const submitting = ref(false)
const showQuoteModal = ref(false)
const showLoginRoleModal = ref(false)
const showSuccessModal = ref(false)
const submittedQuoteDetails = ref(null)
const quoteType = ref('kurumsal')
const searchQuery = ref('')

const quoteStep = ref(1) // 1: Auth, 2: Documents, 3: Quote Details
const authMode = ref('register') // 'register' or 'login'
const authPassword = ref('')

const docFiles = reactive({
  tax_plate: '',
  signature_circular: '',
  activity_certificate: '',
  trade_registry: ''
})

const selectedTypeTitle = computed(() => {
  if (quoteType.value === 'bireysel') return 'Bireysel'
  if (quoteType.value === 'r2r') return 'R2R'
  return 'Kurumsal'
})

const form = reactive({
  company_name: '',
  email: '',
  phone: '',
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  vehicle_count: 5,
  duration_months: 36,
  estimated_annual_mileage: 20000
})

const onFileSelected = (event, key) => {
  const file = event.target.files[0]
  if (file) {
    docFiles[key] = file.name
  }
}

const openQuoteModal = async (type = 'kurumsal') => {
  quoteType.value = type

  const token = localStorage.getItem('fleetcar_token')
  const customerId = localStorage.getItem('fleetcar_customer_id')

  if (token && customerId) {
    // Already logged in - redirect directly to quotes management page in panel
    router.push('/dashboard/quotes')
    return
  }

  const userEmail = localStorage.getItem('fleetcar_user_email')
  const customerName = localStorage.getItem('fleetcar_customer_name')

  if (userEmail) form.email = userEmail
  if (customerName) form.company_name = customerName

  showQuoteModal.value = true
  quoteStep.value = 1
  authMode.value = 'register'
}

const handleModalRegister = async () => {
  if (!form.email || !authPassword.value) return
  submitting.value = true

  try {
    const res = await fetch('/api/customer/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.email,
        password: authPassword.value,
        company_name: form.company_name,
        phone: form.phone
      })
    })

    if (res.ok) {
      const data = await res.json()
      const cust = data.customer || {}

      localStorage.setItem('fleetcar_token', data.token)
      localStorage.setItem('fleetcar_customer_id', String(cust.id || '1'))
      localStorage.setItem('fleetcar_customer_name', cust.company_name || form.company_name || 'Müşteri Firma')
      localStorage.setItem('fleetcar_user_email', cust.email || form.email)
      localStorage.setItem('fleet_customer', JSON.stringify(cust))

      showQuoteModal.value = false
      // Redirect to company documents settings tab or quotes page in panel
      router.push('/dashboard/settings?tab=sirket_evraklari')
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || 'Kayıt yapılırken bir sorun oluştu.')
    }
  } catch (err) {
    console.error('Modal register error:', err)
    alert('Sunucuya bağlanılamadı.')
  } finally {
    submitting.value = false
  }
}

const handleModalLogin = async () => {
  if (!form.email || !authPassword.value) return
  submitting.value = true

  try {
    const res = await fetch('/api/customer/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.email,
        password: authPassword.value
      })
    })

    if (res.ok) {
      const data = await res.json()
      const cust = data.customer || {}

      localStorage.setItem('fleetcar_token', data.token)
      localStorage.setItem('fleetcar_customer_id', String(cust.id || '1'))
      localStorage.setItem('fleetcar_customer_name', cust.company_name || 'Müşteri Firma')
      localStorage.setItem('fleetcar_user_email', cust.email || form.email)
      localStorage.setItem('fleet_customer', JSON.stringify(cust))

      showQuoteModal.value = false
      router.push('/dashboard/quotes')
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || 'Giriş yapılamadı!')
    }
  } catch (err) {
    console.error('Modal login error:', err)
    alert('Sunucuya bağlanılamadı.')
  } finally {
    submitting.value = false
  }
}

const handleModalDocuments = async () => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  if (!customerId) {
    alert('Lütfen önce kayıt olun veya giriş yapın.')
    quoteStep.value = 1
    return
  }

  submitting.value = true
  try {
    const res = await fetch('/api/customer/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: Number(customerId),
        tax_plate: docFiles.tax_plate || 'vergi_levhasi.pdf',
        signature_circular: docFiles.signature_circular || 'imza_sirkusu.pdf',
        activity_certificate: docFiles.activity_certificate || 'faaliyet_belgesi.pdf',
        trade_registry: docFiles.trade_registry || 'ticaret_sicil_gazetesi.pdf'
      })
    })

    if (res.ok) {
      quoteStep.value = 3
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || 'Evraklar kaydedilirken sorun oluştu.')
    }
  } catch (err) {
    console.error('Modal documents error:', err)
    alert('Sunucuya bağlanılamadı.')
  } finally {
    submitting.value = false
  }
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    openQuoteModal('kurumsal')
  }
}

const calculatedPrice = computed(() => {
  const basePrice = 12000
  const segmentMultipliers = { "A": 0.70, "B": 0.85, "C": 1.0, "D": 1.30, "E": 1.70 }
  const segMult = segmentMultipliers[form.vehicle_segment] || 1.0
  
  const typeMultipliers = { "Sedan": 1.0, "SUV": 1.20, "Hatchback": 0.95, "Hafif Ticari": 1.15 }
  const typeMult = typeMultipliers[form.vehicle_type] || 1.0
  
  const durationMultipliers = { 12: 1.0, 24: 0.90, 36: 0.82, 48: 0.75 }
  const durMult = durationMultipliers[form.duration_months] || 0.90
  
  const mileageMultipliers = { 10000: 0.95, 20000: 1.0, 30000: 1.12, 40000: 1.25 }
  const kmMult = mileageMultipliers[form.estimated_annual_mileage] || 1.0
  
  const pricePerVehicle = basePrice * segMult * typeMult * durMult * kmMult
  return Math.round(pricePerVehicle * form.vehicle_count)
})

const calculatedPriceFormatted = computed(() => {
  return calculatedPrice.value.toLocaleString('tr-TR')
})

const submitQuote = async () => {
  submitting.value = true
  try {
    const response = await fetch('/api/quotes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(form)
    })
    
    if (response.ok) {
      const data = await response.json()
      submittedQuoteDetails.value = data
      showQuoteModal.value = false
      showSuccessModal.value = true
    } else {
      alert('Teklif oluşturulurken bir sorun oluştu.')
    }
  } catch (error) {
    console.error('API Error:', error)
    alert('Backend bağlantı hatası oluştu.')
  } finally {
    submitting.value = false
  }
}

const goToLogin = () => {
  showSuccessModal.value = false
  router.push('/dashboard')
}
</script>

