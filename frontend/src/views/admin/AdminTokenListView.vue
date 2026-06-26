<script setup lang="ts">
import { computed, ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { Plus } from '@lucide/vue'
import DataTablePage from '@/components/DataTablePage.vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api, formatApiError, type PaginatedResponse } from '@/api/client'
import { confirmAction } from '@/composables/useConfirm'
import { useAdminList } from '@/composables/useAdminList'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'

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
const { emptyMessage } = useEmptyTableMessage({
  query,
  search,
  entity: 'tokens',
  scope: 'global',
})
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
  if (!(await confirmAction({
    title: 'Revoke token',
    message: 'Revoke this token?',
    confirmLabel: 'Revoke',
  }))) return
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
    :empty-message="emptyMessage"
    :selected="selected"
    :selectable="false"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
  >
    <template #actions>
      <AppButton variant="primary" size="sm" class="inline-flex items-center gap-1" @click="dialogOpen = true">
        <Plus class="h-4 w-4" />
        Add token
      </AppButton>
    </template>
    <template #filters>
      <input v-model="search" class="aots-field max-w-xs" placeholder="Search tokens or users…" />
    </template>
    <template #cell-actions="{ row }">
      <AppButton variant="ghost-danger" size="sm" @click="deleteToken(row.pk)">
        Revoke
      </AppButton>
    </template>
  </DataTablePage>

  <div
    v-if="dialogOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-aots-overlay p-4"
    @click.self="dialogOpen = false"
  >
    <div class="w-full max-w-md space-y-4 rounded-xl border border-aots bg-aots-page p-5">
      <h3 class="text-lg font-medium">Create token</h3>
      <select v-model="selectedUserId" class="aots-select w-full">
        <option value="">Select user…</option>
        <option v-for="user in usersQuery.data.value?.results ?? []" :key="user.id" :value="user.id">
          {{ user.username }}
        </option>
      </select>
      <AppAlert v-if="formError" kind="error">{{ formError }}</AppAlert>
      <div class="flex justify-end gap-2">
        <AppButton variant="ghost" @click="dialogOpen = false">Cancel</AppButton>
        <AppButton variant="primary" :disabled="creating" @click="createToken">
          {{ creating ? 'Creating…' : 'Create' }}
        </AppButton>
      </div>
    </div>
  </div>
</template>
