<template>
  <div id="app">
    <ImpersonationBanner />
    <router-view />
    <EmailVerificationModal />
    <AppFeedback />
  </div>
</template>

<script setup>
import AppFeedback from './components/AppFeedback.vue'
import EmailVerificationModal from './components/EmailVerificationModal.vue'
import ImpersonationBanner from './components/ImpersonationBanner.vue'
</script>
