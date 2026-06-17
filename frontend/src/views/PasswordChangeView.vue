<script setup lang="ts">
import { ref } from 'vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api } from '@/api/client'

const oldPassword = ref('')
const newPassword1 = ref('')
const newPassword2 = ref('')
const message = ref('')

async function submit() {
  message.value = ''
  await api('/api/auth/password-change/', {
    method: 'POST',
    body: {
      old_password: oldPassword.value,
      new_password1: newPassword1.value,
      new_password2: newPassword2.value,
    },
  })
  message.value = 'Password updated.'
}
</script>

<template>
  <div class="max-w-md space-y-4">
    <h1 class="text-2xl font-semibold">Change password</h1>
    <form class="space-y-3" @submit.prevent="submit">
      <input v-model="oldPassword" type="password" class="aots-field" placeholder="Current password" />
      <input v-model="newPassword1" type="password" class="aots-field" placeholder="New password" />
      <input v-model="newPassword2" type="password" class="aots-field" placeholder="Confirm new password" />
      <AppButton type="submit" variant="primary">Update</AppButton>
    </form>
    <AppAlert v-if="message" kind="success">{{ message }}</AppAlert>
  </div>
</template>
