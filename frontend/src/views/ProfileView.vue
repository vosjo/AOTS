<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api, formatApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const token = ref<string | null>(null)
const apiKey = ref<string | null>(null)
const apiSecret = ref<string | null>(null)
const error = ref('')

onMounted(async () => {
  try {
    await auth.fetchMe()
    if (auth.isAuthenticated) {
      const res = await api<{ token: string }>('/api/auth/token/')
      token.value = res.token
      const creds = await api<{ api_key: string | null; has_api_secret: boolean }>(
        '/api/me/credentials/',
      )
      apiKey.value = creds.api_key
    }
  } catch (err) {
    error.value = formatApiError(err)
  }
})

async function regenerateToken() {
  error.value = ''
  try {
    const res = await api<{ token: string }>('/api/auth/token/', { method: 'POST' })
    token.value = res.token
  } catch (err) {
    error.value = formatApiError(err)
  }
}

async function regenerateApiKey() {
  error.value = ''
  try {
    const res = await api<{ api_key: string; api_secret: string }>('/api/auth/api-key/', { method: 'POST' })
    apiKey.value = res.api_key
    apiSecret.value = res.api_secret
    await auth.fetchMe()
  } catch (err) {
    error.value = formatApiError(err)
  }
}
</script>

<template>
  <div class="space-y-6 max-w-2xl">
    <h1 class="text-2xl font-semibold">Your profile</h1>
    <p v-if="auth.user?.username">Signed in as <strong>{{ auth.user.username }}</strong></p>

    <section class="aots-panel space-y-2">
      <h2 class="font-medium text-aots-heading">DRF token</h2>
      <code class="block break-all rounded-md border border-aots bg-aots-surface-muted p-2 text-sm text-aots">{{ token }}</code>
      <AppButton variant="link" @click="regenerateToken">Regenerate token</AppButton>
    </section>

    <section class="aots-panel space-y-2">
      <h2 class="font-medium">API key pair</h2>
      <p class="text-sm text-aots">Public key: {{ apiKey || '—' }}</p>
      <AppButton variant="link" @click="regenerateApiKey">Generate new API key</AppButton>
      <AppAlert v-if="apiSecret" kind="warning">
        Secret (shown once): {{ apiSecret }}
      </AppAlert>
    </section>

    <AppButton variant="link" to="/accounts/password_change/">Change password</AppButton>
    <AppAlert v-if="error" kind="error">{{ error }}</AppAlert>
  </div>
</template>
