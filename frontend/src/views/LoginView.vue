<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

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
    const next = (route.query.next as string) || '/w/projects/'
    router.push(next)
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
      <button type="submit" class="aots-btn-primary w-full">Sign in</button>
    </form>
    <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>
  </div>
</template>
