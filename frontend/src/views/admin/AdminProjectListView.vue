<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import DataTablePage from '@/components/DataTablePage.vue'
import { useAdminList } from '@/composables/useAdminList'

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
    :selected="selected"
    :selectable="false"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
  >
    <template #actions>
      <RouterLink to="/admin/projects/new" class="aots-btn-primary inline-flex items-center gap-1 text-sm">
        <Plus class="h-4 w-4" />
        Add project
      </RouterLink>
    </template>
    <template #filters>
      <input v-model="search" class="aots-field max-w-xs" placeholder="Search projects…" />
    </template>
    <template #cell-actions="{ row }">
      <RouterLink :to="`/admin/projects/${row.pk}`" class="text-sm text-sky-400 hover:text-sky-300">
        Edit
      </RouterLink>
    </template>
  </DataTablePage>
</template>
