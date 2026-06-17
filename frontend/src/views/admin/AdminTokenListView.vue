<script setup lang="ts">
import { computed, ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { Plus } from 'lucide-vue-next'
import DataTablePage from '@/components/DataTablePage.vue'
import AppAlert from '@/components/AppAlert.vue'
import { api, formatApiError, type PaginatedResponse } from '@/api/client'
import { useAdminList } from '@/composables/useAdminList'

interface AdminTokenRow {
  pk: number
  key: string
  user: number
  username: string
  created: string
}

interface UserChoice {
  id: number
  username: string
}

const search = ref('')
const { query, page, pageSize } = useAdminList<AdminTokenRow>({
  endpoint: '/api/admin/tokens/',
  search,
})

const rows = computed(() => query.data.value?.results ?? [])
const selected = ref(new Set<number>())

const columns = [
  { id: 'key', header: 'Key' },
  { id: 'username', header: 'User' },
  { id: 'created', header: 'Created' },
  { id: 'actions', header: '' },
]

const dialogOpen = ref(false)
const selectedUserId = ref<number | ''>('')
const creating = ref(false)
const formError = ref<string | null>(null)
const queryClient = useQueryClient()

const usersQuery = useQuery({
  queryKey: ['admin-user-choices-tokens'],
  queryFn: () => api<PaginatedResponse<UserChoice>>('/api/admin/users/choices/?page_size=200'),
  enabled: computed(() => dialogOpen.value),
})

async function createToken() {
  if (!selectedUserId.value) {
    formError.value = 'Select a user.'
    return
  }
  creating.value = true
  formError.value = null
  try {
    await api('/api/admin/tokens/', {
      method: 'POST',
      body: { user: selectedUserId.value },
    })
    dialogOpen.value = false
    selectedUserId.value = ''
    await queryClient.invalidateQueries({ queryKey: ['/api/admin/tokens/'] })
  } catch (err) {
    formError.value = formatApiError(err)
  } finally {
    creating.value = false
  }
}

async function deleteToken(pk: number) {
  if (!window.confirm('Revoke this token?')) return
  try {
    await api(`/api/admin/tokens/${pk}/`, { method: 'DELETE' })
    await queryClient.invalidateQueries({ queryKey: ['/api/admin/tokens/'] })
  } catch (err) {
    window.alert(formatApiError(err))
  }
}
</script>

<template>
  <DataTablePage
    title="DRF tokens"
    :columns="columns"
    :rows="rows"
    :count="query.data.value?.count ?? 0"
    :page="page"
    :page-size="pageSize"
    :loading="query.isFetching.value"
    :selected="selected"
    :selectable="false"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
  >
    <template #actions>
      <button type="button" class="aots-btn-primary inline-flex items-center gap-1 text-sm" @click="dialogOpen = true">
        <Plus class="h-4 w-4" />
        Add token
      </button>
    </template>
    <template #filters>
      <input v-model="search" class="aots-field max-w-xs" placeholder="Search tokens or users…" />
    </template>
    <template #cell-actions="{ row }">
      <button type="button" class="text-sm text-red-400 hover:text-red-300" @click="deleteToken(row.pk)">
        Revoke
      </button>
    </template>
  </DataTablePage>

  <div
    v-if="dialogOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
    @click.self="dialogOpen = false"
  >
    <div class="w-full max-w-md space-y-4 rounded-xl border border-slate-600 bg-slate-900 p-5">
      <h3 class="text-lg font-medium">Create token</h3>
      <select v-model="selectedUserId" class="aots-select w-full">
        <option value="">Select user…</option>
        <option v-for="user in usersQuery.data.value?.results ?? []" :key="user.id" :value="user.id">
          {{ user.username }}
        </option>
      </select>
      <AppAlert v-if="formError" kind="error">{{ formError }}</AppAlert>
      <div class="flex justify-end gap-2">
        <button type="button" class="aots-btn-secondary" @click="dialogOpen = false">Cancel</button>
        <button type="button" class="aots-btn-primary" :disabled="creating" @click="createToken">
          {{ creating ? 'Creating…' : 'Create' }}
        </button>
      </div>
    </div>
  </div>
</template>
