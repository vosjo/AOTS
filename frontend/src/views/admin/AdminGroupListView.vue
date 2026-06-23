<script setup lang="ts">
import { computed, ref } from 'vue'
import { Plus } from '@lucide/vue'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import { rowPk, useAdminList } from '@/composables/useAdminList'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'

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
const { emptyMessage } = useEmptyTableMessage({
  query,
  search,
  entity: 'groups',
  scope: 'global',
})

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
    :empty-message="emptyMessage"
    :selected="selected"
    :selectable="false"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
  >
    <template #actions>
      <AppButton variant="primary" size="sm" class="inline-flex items-center gap-1" to="/admin/groups/new">
        <Plus class="h-4 w-4" />
        Add group
      </AppButton>
    </template>
    <template #filters>
      <input v-model="search" class="aots-field max-w-xs" placeholder="Search groups…" />
    </template>
    <template #cell-actions="{ row }">
      <AppButton variant="link" :to="`/admin/groups/${rowPk(row)}`">
        Edit
      </AppButton>
    </template>
  </DataTablePage>
</template>
