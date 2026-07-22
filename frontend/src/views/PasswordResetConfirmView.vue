<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api, formatApiError } from '@/api/client'

const route = useRoute()
const router = useRouter()
const uidb64 = String(route.params.uidb64)
const token = String(route.params.token)

const newPassword1 = ref('')
const newPassword2 = ref('')
const loading = ref(true)
const busy = ref(false)
const linkError = ref('')
const error = ref('')

onMounted(async () => {
  try {
    await api<{ valid: boolean }>(
      `/api/auth/password-reset/validate/?uid=${encodeURIComponent(uidb64)}&token=${encodeURIComponent(token)}`,
    )
  } catch (e) {
    linkError.value = formatApiError(e)
  } finally {
    loading.value = false
  }
})

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await api('/api/auth/password-reset/confirm/', {
      method: 'POST',
      body: {
        uid: uidb64,
        token,
        new_password1: newPassword1.value,
        new_password2: newPassword2.value,
      },
    })
    await router.push('/accounts/reset/done/')
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="max-w-sm mx-auto mt-16 space-y-4">
    <h1 class="text-2xl font-semibold">Choose a new password</h1>

    <p v-if="loading" class="text-sm text-aots-muted">Checking reset link…</p>

    <template v-else-if="linkError">
      <AppAlert kind="error" title="Invalid reset link">{{ linkError }}</AppAlert>
      <AppButton variant="link" to="/accounts/password_reset/">Request a new link</AppButton>
    </template>

    <template v-else>
      <p class="text-sm text-aots-muted">
        Choose a new password for your account.
      </p>
      <form class="space-y-3" @submit.prevent="submit">
        <input
          v-model="newPassword1"
          type="password"
          required
          autocomplete="new-password"
          class="aots-field"
          placeholder="New password"
        />
        <input
          v-model="newPassword2"
          type="password"
          required
          autocomplete="new-password"
          class="aots-field"
          placeholder="Confirm new password"
        />
        <AppButton type="submit" variant="primary" class="w-full" :disabled="busy">
          Update password
        </AppButton>
      </form>
      <AppAlert v-if="error" kind="error">{{ error }}</AppAlert>
    </template>
  </div>
</template>
