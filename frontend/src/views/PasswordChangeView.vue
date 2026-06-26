<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api, formatApiError, setCsrfToken } from '@/api/client'

const router = useRouter()
const oldPassword = ref('')
const newPassword1 = ref('')
const newPassword2 = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    const res = await api<{ detail: string; csrfToken?: string }>('/api/auth/password-change/', {
      method: 'POST',
      body: {
        old_password: oldPassword.value,
        new_password1: newPassword1.value,
        new_password2: newPassword2.value,
      },
    })
    if (res.csrfToken) {
      setCsrfToken(res.csrfToken)
    }
    await router.push('/accounts/password_change/done/')
  } catch (err) {
    error.value = formatApiError(err)
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-16 space-y-4">
    <h1 class="text-2xl font-semibold">Change password</h1>
    <form class="space-y-3" @submit.prevent="submit">
      <input v-model="oldPassword" type="password" class="aots-field" placeholder="Current password" autocomplete="current-password" />
      <input v-model="newPassword1" type="password" class="aots-field" placeholder="New password" autocomplete="new-password" />
      <input v-model="newPassword2" type="password" class="aots-field" placeholder="Confirm new password" autocomplete="new-password" />
      <AppButton type="submit" variant="primary">Update</AppButton>
    </form>
    <AppButton variant="link" to="/users/you/">Back to profile</AppButton>
    <AppAlert v-if="error" kind="error">{{ error }}</AppAlert>
  </div>
</template>
