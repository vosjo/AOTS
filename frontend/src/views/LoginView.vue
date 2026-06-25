<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { useAuthStore } from '@/stores/auth'
import { safeRedirectPath } from '@/utils/safeRedirect'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push(safeRedirectPath(route.query.next))
  } catch {
    error.value = 'Invalid credentials.'
  }
}
</script>

<template>
  <div class="max-w-sm mx-auto mt-16 space-y-4">
    <h1 class="text-2xl font-semibold">Login</h1>
    <form class="space-y-3" @submit.prevent="submit">
      <input v-model="username" class="aots-field" placeholder="Username" />
      <input v-model="password" type="password" class="aots-field" placeholder="Password" />
      <AppButton type="submit" variant="primary" class="w-full">Sign in</AppButton>
    </form>
    <AppAlert v-if="error" kind="error">{{ error }}</AppAlert>
  </div>
</template>
