<template>
  <div id="app">
    <router-view />
    <EmailVerificationModal />
  </div>
</template>

<script setup>
import EmailVerificationModal from './components/EmailVerificationModal.vue'
</script>
