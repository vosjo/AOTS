<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Plus } from '@lucide/vue'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import { rowPk, useAdminList } from '@/composables/useAdminList'

interface AdminUserRow {
  id: number
  pk: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  is_student: boolean
  note: string
}

const search = ref('')
const filters = ref({
  is_active: '' as string,
  is_staff: '' as string,
  is_superuser: '' as string,
  is_student: '' as string,
})

const { query, page, pageSize } = useAdminList<AdminUserRow>({
  endpoint: '/api/admin/users/',
  search,
  filters,
})

const rows = computed(() =>
  (query.data.value?.results ?? []).map((row) => ({ ...row, pk: row.id })),
)

const columns = [
  { id: 'username', header: 'Username' },
  { id: 'email', header: 'Email' },
  { id: 'name', header: 'Name', accessor: (row: AdminUserRow) => `${row.first_name} ${row.last_name}`.trim() || '—' },
  { id: 'is_active', header: 'Active', accessor: (row: AdminUserRow) => (row.is_active ? 'Yes' : 'No') },
  { id: 'is_staff', header: 'Staff', accessor: (row: AdminUserRow) => (row.is_staff ? 'Yes' : 'No') },
  { id: 'is_student', header: 'Student', accessor: (row: AdminUserRow) => (row.is_student ? 'Yes' : 'No') },
  { id: 'is_superuser', header: 'Superuser', accessor: (row: AdminUserRow) => (row.is_superuser ? 'Yes' : 'No') },
  { id: 'note', header: 'Note' },
  { id: 'actions', header: '' },
]

const selected = ref(new Set<number>())
</script>

<template>
  <DataTablePage
    title="Users"
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
      <AppButton variant="primary" size="sm" class="inline-flex items-center gap-1" to="/admin/users/new">
        <Plus class="h-4 w-4" />
        Add user
      </AppButton>
    </template>
    <template #filters>
      <div class="flex flex-wrap gap-2">
        <input v-model="search" class="aots-field max-w-xs" placeholder="Search users…" />
        <select v-model="filters.is_active" class="aots-select w-auto">
          <option value="">Active: all</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
        <select v-model="filters.is_staff" class="aots-select w-auto">
          <option value="">Staff: all</option>
          <option value="true">Staff</option>
          <option value="false">Not staff</option>
        </select>
        <select v-model="filters.is_superuser" class="aots-select w-auto">
          <option value="">Superuser: all</option>
          <option value="true">Superuser</option>
          <option value="false">Not superuser</option>
        </select>
        <select v-model="filters.is_student" class="aots-select w-auto">
          <option value="">Student: all</option>
          <option value="true">Student</option>
          <option value="false">Not student</option>
        </select>
      </div>
    </template>
    <template #cell-actions="{ row }">
      <AppButton variant="link" :to="`/admin/users/${rowPk(row)}`">
        Edit
      </AppButton>
    </template>
  </DataTablePage>
</template>
