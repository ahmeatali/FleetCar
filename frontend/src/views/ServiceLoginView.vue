<template>
  <div style="min-height: 100vh; background: #f8fafc; display: flex; flex-direction: column;">
    <!-- Top Header Bar -->
    <header class="hero-dark-bg" style="padding: 16px 8%; text-align: left; height: 60px; display: flex; align-items: center;">
      <router-link to="/" class="nav-logo" style="text-decoration: none;">
        <div class="nav-logo-icon" style="background: #2563eb; border-radius: 8px;">⇄</div>
        <span style="font-weight: 800; font-size: 1.4rem; color: #ffffff;">FleetRent <span style="color: #93c5fd; font-size: 0.85rem; font-weight: 600;">Servis</span></span>
      </router-link>
    </header>

    <!-- Main Container - Perfectly Centered -->
    <main style="flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px;">
      <div class="glass-panel auth-card fade-in-up" style="max-width: 480px; width: 100%; padding: 40px; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
        <div class="nav-logo" style="justify-content: center; margin-bottom: 25px;">
          <div class="nav-logo-icon" style="background: linear-gradient(135deg, #2563eb, #1d4ed8); border-radius: 8px;">🔧</div>
          <span style="font-size: 1.6rem; font-weight: 800; color: #0f172a;">FleetRent <span style="color: #2563eb; font-size: 0.85rem; vertical-align: super; font-weight: 600;">Servis</span></span>
        </div>

        <h2 style="font-size: 1.5rem; text-align: center; margin-bottom: 8px; color: #0f172a; font-weight: 800;">Servis Girişi</h2>
        <p style="color: #64748b; font-size: 0.9rem; text-align: center; margin-bottom: 25px; line-height: 1.5;">
          <strong>Bakım/Onarım, Lastik Hizmetleri & Oto Kurtarma</strong> noktaları için e-posta ve şifre ile portal girişi.
        </p>

        <form @submit.prevent="handleLogin">
          <div class="form-group" style="margin-bottom: 18px;">
            <label class="form-label" style="font-weight: 600; color: #334155; font-size: 0.88rem;">Servis E-posta Adresi</label>
            <input 
              type="email" 
              v-model="email" 
              required 
              class="form-input" 
              placeholder="servis@sirket.com"
              style="height: 48px; font-size: 0.95rem;"
            >
          </div>

          <div class="form-group" style="margin-bottom: 25px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <label class="form-label" style="font-weight: 600; color: #334155; font-size: 0.88rem; margin: 0;">Giriş Şifresi</label>
              <a href="#" style="font-size: 0.8rem; color: #2563eb; text-decoration: none;">Şifremi Unuttum?</a>
            </div>
            <input 
              type="password" 
              v-model="password" 
              required 
              class="form-input" 
              placeholder="••••••••"
              style="height: 48px;"
            >
          </div>

          <button type="submit" class="btn btn-block" style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; padding: 14px; font-size: 1rem; font-weight: 700; border: none; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3); width: 100%;">
            Servis Portaline Giriş Yap ➔
          </button>
        </form>

        <div style="margin-top: 25px; display: flex; flex-direction: column; gap: 10px; text-align: center;">
          <router-link to="/supplier-login" style="color: #10b981; font-size: 0.85rem; font-weight: 600; text-decoration: none;" class="hover-underline">
            🏭 Tedarikçi Girişine Git (Araba Sağlayıcı & Kiralama) →
          </router-link>
          <router-link to="/login" style="color: #64748b; font-size: 0.85rem; text-decoration: none;" class="hover-underline">
            ← Müşteri Portalı Girişine Dön
          </router-link>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password = ref('')

const handleLogin = async () => {
  if (!email.value) return
  
  const searchMail = email.value.toLowerCase().trim()
  const domainName = searchMail.split('@')[1] ? searchMail.split('@')[1].split('.')[0] : 'Servis'
  const serviceName = domainName.charAt(0).toUpperCase() + domainName.slice(1) + ' Oto Servis'
  
  try {
    const res = await fetch('/api/suppliers')
    let supplier = null
    if (res.ok) {
      const list = await res.json()
      supplier = list.find(s => s.name.toLowerCase() === serviceName.toLowerCase())
    }
    
    if (!supplier) {
      const createRes = await fetch('/api/suppliers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: serviceName,
          type: 'servis',
          phone: '0850 111 0000',
          city: 'İstanbul',
          district: 'Merkez',
          services: ['Periyodik Bakım', 'Mekanik Onarım'],
          contract_type: 'Anlaşmalı'
        })
      })
      if (createRes.ok) {
        supplier = await createRes.json()
      }
    }
    
    const supplierId = supplier ? supplier.id : Date.now()
    const finalName = supplier ? supplier.name : serviceName
    
    localStorage.setItem('fleetcar_supplier_id', String(supplierId))
    localStorage.setItem('fleetcar_supplier_name', finalName)
    localStorage.setItem('fleetcar_supplier_type', 'servis')
    localStorage.setItem('fleetcar_supplier_email', searchMail)
    localStorage.setItem('fleet_supplier', JSON.stringify({
      id: supplierId,
      name: finalName,
      type: 'servis',
      city: supplier?.city || 'İstanbul',
      district: supplier?.district || 'Merkez',
      contract_type: supplier?.contract_type || 'Anlaşmalı',
      services: supplier?.services || ['Periyodik Bakım', 'Mekanik Onarım'],
      phone: supplier?.phone || '0850 111 0000'
    }))
    
    router.push('/supplier-portal')
  } catch (err) {
    console.error('Login error:', err)
    localStorage.setItem('fleetcar_supplier_id', '1')
    localStorage.setItem('fleetcar_supplier_name', serviceName)
    localStorage.setItem('fleetcar_supplier_type', 'servis')
    localStorage.setItem('fleetcar_supplier_email', searchMail)
    router.push('/supplier-portal')
  }
}
</script>
