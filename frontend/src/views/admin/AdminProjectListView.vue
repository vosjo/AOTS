<script setup lang="ts">
import { computed, ref } from 'vue'
import { Plus } from '@lucide/vue'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import { useAdminList } from '@/composables/useAdminList'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'

interface AdminProjectRow {
  pk: number
  name: string
  slug: string
  description: string
  is_public: boolean
}

const search = ref('')
const { query, page, pageSize } = useAdminList<AdminProjectRow>({
  endpoint: '/api/admin/projects/',
  search,
})

const rows = computed(() => query.data.value?.results ?? [])
const { emptyMessage } = useEmptyTableMessage({
  query,
  search,
  entity: 'projects',
  scope: 'global',
})

const columns = [
  { id: 'name', header: 'Name' },
  { id: 'slug', header: 'Slug' },
  { id: 'is_public', header: 'Public', accessor: (row: AdminProjectRow) => (row.is_public ? 'Yes' : 'No') },
  { id: 'description', header: 'Description' },
  { id: 'actions', header: '' },
]

const selected = ref(new Set<number>())
</script>

<template>
  <DataTablePage
    title="Projects"
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
      <AppButton variant="primary" size="sm" class="inline-flex items-center gap-1" to="/admin/projects/new">
        <Plus class="h-4 w-4" />
        Add project
      </AppButton>
    </template>
    <template #filters>
      <input v-model="search" class="aots-field max-w-xs" placeholder="Search projects…" />
    </template>
    <template #cell-actions="{ row }">
      <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
        <AppButton variant="link" :to="`/admin/projects/${row.pk}`">
          Edit
        </AppButton>
        <AppButton variant="link" :to="`/w/${row.slug}/settings/consensus/`">
          Consensus
        </AppButton>
      </div>
    </template>
  </DataTablePage>
</template>
