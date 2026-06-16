import { VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { initAppBootstrap } from '@/composables/useAppBootstrap'
import router from './router'
import './style.css'

async function start() {
  await initAppBootstrap()

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.use(VueQueryPlugin)
  app.mount('#app')
}

start()
