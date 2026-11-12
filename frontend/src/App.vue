<template>
  <div id="app">
    <ImpersonationBanner />
    <router-view />
    <EmailVerificationModal />
  </div>
</template>

<script setup>
import EmailVerificationModal from './components/EmailVerificationModal.vue'
import ImpersonationBanner from './components/ImpersonationBanner.vue'
</script>
