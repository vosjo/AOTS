<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import DataTablePage from '@/components/DataTablePage.vue'
import { rowPk, useAdminList } from '@/composables/useAdminList'

interface AdminGroupRow {
  id: number
  pk: number
  name: string
  permission_count: number
}

const search = ref('')
const { query, page, pageSize } = useAdminList<AdminGroupRow>({
  endpoint: '/api/admin/groups/',
  search,
})

const rows = computed(() =>
  (query.data.value?.results ?? []).map((row) => ({ ...row, pk: row.id })),
)

const columns = [
  { id: 'name', header: 'Name' },
  { id: 'permission_count', header: 'Permissions' },
  { id: 'actions', header: '' },
]

const selected = ref(new Set<number>())
</script>

<template>
  <DataTablePage
    title="Groups"
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
      <RouterLink to="/admin/groups/new" class="aots-btn-primary inline-flex items-center gap-1 text-sm">
        <Plus class="h-4 w-4" />
        Add group
      </RouterLink>
    </template>
    <template #filters>
      <input v-model="search" class="aots-field max-w-xs" placeholder="Search groups…" />
    </template>
    <template #cell-actions="{ row }">
      <RouterLink :to="`/admin/groups/${rowPk(row)}`" class="text-sm text-sky-400 hover:text-sky-300">
        Edit
      </RouterLink>
    </template>
  </DataTablePage>
</template>
