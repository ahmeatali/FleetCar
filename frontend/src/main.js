import { createApp } from 'vue'
import './design-tokens.css'
import './style.css'
import './mobile-tables.css'
import App from './App.vue'
import router from './router'

import { installPortalFetch } from './utils/portalFetch'
import { installTableCards } from './utils/tableCards'
installPortalFetch()

createApp(App).use(router).mount('#app')
installTableCards()
