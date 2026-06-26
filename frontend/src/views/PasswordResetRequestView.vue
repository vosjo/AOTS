<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api, formatApiError } from '@/api/client'

const router = useRouter()
const email = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await api('/api/auth/password-reset/', {
      method: 'POST',
      body: { email: email.value.trim() },
    })
    await router.push('/accounts/password_reset/done/')
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="max-w-sm mx-auto mt-16 space-y-4">
    <h1 class="text-2xl font-semibold">Reset password</h1>
    <p class="text-sm text-aots-muted">
      Enter the email address linked to your account. We will send you a reset link.
    </p>
    <form class="space-y-3" @submit.prevent="submit">
      <input
        v-model="email"
        type="email"
        required
        autocomplete="email"
        class="aots-field"
        placeholder="Email address"
      />
      <AppButton type="submit" variant="primary" class="w-full" :disabled="busy">
        Send reset link
      </AppButton>
    </form>
    <AppButton variant="link" to="/accounts/login/">Back to login</AppButton>
    <AppAlert v-if="error" kind="error">{{ error }}</AppAlert>
  </div>
</template>
