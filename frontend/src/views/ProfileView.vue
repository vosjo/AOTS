<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const token = ref<string | null>(null)
const apiKey = ref<string | null>(null)
const apiSecret = ref<string | null>(null)

onMounted(async () => {
  await auth.fetchMe()
  if (auth.isAuthenticated) {
    const res = await api<{ token: string }>('/api/auth/token/')
    token.value = res.token
  }
})

async function regenerateToken() {
  const res = await api<{ token: string }>('/api/auth/token/', { method: 'POST' })
  token.value = res.token
}

async function regenerateApiKey() {
  const res = await api<{ api_key: string; api_secret: string }>('/api/auth/api-key/', { method: 'POST' })
  apiKey.value = res.api_key
  apiSecret.value = res.api_secret
  await auth.fetchMe()
}
</script>

<template>
  <div class="space-y-6 max-w-2xl">
    <h1 class="text-2xl font-semibold">Your profile</h1>
    <p v-if="auth.user?.username">Signed in as <strong>{{ auth.user.username }}</strong></p>

    <section class="aots-panel space-y-2">
      <h2 class="font-medium text-slate-50">DRF token</h2>
      <code class="block break-all rounded-md border border-slate-500 bg-slate-700 p-2 text-sm text-slate-100">{{ token }}</code>
      <AppButton variant="link" @click="regenerateToken">Regenerate token</AppButton>
    </section>

    <section class="aots-panel space-y-2">
      <h2 class="font-medium">API key pair</h2>
      <p class="text-sm text-slate-200">Public key: {{ auth.user?.api_key || '—' }}</p>
      <AppButton variant="link" @click="regenerateApiKey">Generate new API key</AppButton>
      <AppAlert v-if="apiSecret" kind="warning">
        Secret (shown once): {{ apiSecret }}
      </AppAlert>
    </section>

    <AppButton variant="link" to="/accounts/password_change/">Change password</AppButton>
  </div>
</template>
