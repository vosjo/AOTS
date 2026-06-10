<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DataTablePage from '@/components/DataTablePage.vue'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const projectSlug = computed(() => useRoute().params.projectSlug as string)
const auth = useAuthStore()

const { query, page, pageSize, selected, toggleRow, toggleAll } = useDataTablePage<{
  pk: number; name: string; slug: string
}>({ endpoint: '/api/analysis/methods/', projectSlug })
const rows = computed(() => query.data.value?.results ?? [])

async function deleteMethod(pk: number) {
  if (!confirm('Delete method? This will delete all datasets with this method!')) return
  await api(`/api/analysis/methods/${pk}/`, { method: 'DELETE' })
  await query.refetch()
}
</script>

<template>
  <DataTablePage
    title="Methods"
    :columns="[
      { id: 'name', header: 'Name' },
      { id: 'slug', header: 'Slug' },
    ]"
    :rows="rows"
    :count="query.data.value?.count ?? 0"
    :page="page"
    :page-size="pageSize"
    :loading="query.isFetching.value"
    :selected="selected"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
    @toggle-row="toggleRow"
    @toggle-all="toggleAll(rows)"
  >
    <template #cell-name="{ row }">
      <span>{{ row.name }}</span>
      <button
        v-if="auth.isAuthenticated"
        class="ml-2 text-red-400 text-xs"
        @click.stop="deleteMethod(row.pk)"
      >
        Delete
      </button>
    </template>
  </DataTablePage>
</template>
