import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { initAppBootstrap } from '@/composables/useAppBootstrap'
import { queryClient } from '@/queryClient'
import { initTheme } from '@/theme'
import router from './router'
import './style.css'

async function start() {
  initTheme()
  await initAppBootstrap()

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.use(VueQueryPlugin, { queryClient })
  app.mount('#app')
}

start()
