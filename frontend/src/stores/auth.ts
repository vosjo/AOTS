import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api, setCsrfToken, type MeResponse } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<MeResponse | null>(null)
  const loaded = ref(false)

  const isAuthenticated = computed(() => user.value?.authenticated === true)
  const isSuperuser = computed(() => user.value?.is_superuser === true)
  const canSyncSimbadAliases = computed(() => isSuperuser.value)

  async function fetchMe() {
    user.value = await api<MeResponse>('/api/me/')
    loaded.value = true
    return user.value
  }

  async function login(username: string, password: string) {
    user.value = await api<MeResponse>('/api/auth/login/', {
      method: 'POST',
      body: { username, password },
    })
    if (user.value.csrfToken) {
      setCsrfToken(user.value.csrfToken)
    }
    return user.value
  }

  async function logout() {
    const data = await api<{ authenticated: boolean; csrfToken?: string }>(
      '/api/auth/logout/',
      { method: 'POST' },
    )
    if (data.csrfToken) {
      setCsrfToken(data.csrfToken)
    }
    user.value = { authenticated: false }
  }

  return { user, loaded, isAuthenticated, isSuperuser, canSyncSimbadAliases, fetchMe, login, logout }
})
