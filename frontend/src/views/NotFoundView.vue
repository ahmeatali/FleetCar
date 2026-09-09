<template>
  <div style="min-height: 100vh; background: #0f172a; color: #ffffff; display: flex; flex-direction: column; position: relative; overflow: hidden;">
    <!-- Background Glow Effects -->
    <div style="position: absolute; top: -10%; left: 50%; transform: translateX(-50%); width: 600px; height: 600px; background: radial-gradient(circle, rgba(124, 58, 237, 0.25) 0%, rgba(59, 130, 246, 0.1) 50%, transparent 70%); pointer-events: none; filter: blur(50px);"></div>
    
    <!-- Top Header Bar -->
    <header style="padding: 20px 8%; display: flex; align-items: center; justify-content: space-between; z-index: 10;">
      <router-link to="/" class="nav-logo" style="text-decoration: none;">
        <div class="nav-logo-icon" style="background: linear-gradient(135deg, #7c3aed, #3b82f6); border-radius: 10px;">⇄</div>
        <span style="font-weight: 800; font-size: 1.5rem; color: #ffffff;">FleetRent</span>
      </router-link>

      <router-link to="/" class="btn btn-secondary" style="border-color: rgba(255,255,255,0.2); color: #e2e8f0; font-size: 0.88rem; text-decoration: none;">
        Anasayfaya Git ➔
      </router-link>
    </header>

    <!-- Main 404 Container -->
    <main style="flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px; z-index: 10;">
      <div class="fade-in-up" style="max-width: 540px; width: 100%; text-align: center; background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 50px 40px; box-shadow: 0 20px 50px rgba(0,0,0,0.4);">
        
        <!-- Animated 404 Badge -->
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 90px; height: 90px; background: rgba(124, 58, 237, 0.15); border: 2px solid rgba(124, 58, 237, 0.4); border-radius: 50%; margin-bottom: 25px; box-shadow: 0 0 30px rgba(124, 58, 237, 0.3);">
          <span style="font-size: 2.5rem; line-height: 1;">🔍</span>
        </div>

        <h1 style="font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; background: linear-gradient(135deg, #c084fc, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          404
        </h1>

        <h2 style="font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-top: 15px; margin-bottom: 12px;">
          Sayfa Bulunamadı
        </h2>

        <p style="color: #94a3b8; font-size: 0.98rem; line-height: 1.6; margin-bottom: 35px; max-width: 440px; margin-left: auto; margin-right: auto;">
          Aradığınız sayfa silinmiş, bağlantı adresi değiştirilmiş veya hiç var olmamış olabilir. Lütfen adresi kontrol edin veya anasayfaya dönün.
        </p>

        <!-- Actions -->
        <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
          <button @click="goBack" class="btn btn-secondary" style="background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.15); color: #cbd5e1; padding: 14px 24px; font-weight: 600; font-size: 0.95rem; cursor: pointer; border-radius: 12px; transition: all 0.2s ease;">
            ← Önceki Sayfaya Dön
          </button>
          
          <router-link to="/" class="btn" style="background: linear-gradient(135deg, #7c3aed, #3b82f6); color: #ffffff; padding: 14px 28px; font-weight: 700; font-size: 0.95rem; text-decoration: none; border-radius: 12px; box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4); transition: transform 0.2s ease, box-shadow 0.2s ease;">
            🏠 Anasayfaya Dön ➔
          </router-link>
        </div>

      </div>
    </main>

    <!-- Footer -->
    <footer style="padding: 20px; text-align: center; font-size: 0.82rem; color: #64748b; z-index: 10;">
      © 2026 FleetRent Filo Yönetimi · All rights reserved.
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.fade-in-up {
  animation: fadeInUp 0.5s ease-out forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
