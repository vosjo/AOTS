<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import DataTablePage from '@/components/DataTablePage.vue'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const bulk = useBulkDownload()
const { query, page, pageSize, selected, toggleRow, toggleAll } = useDataTablePage<{
  pk: number; name: string; valid: boolean
}>({ endpoint: '/api/analysis/datasets/', projectSlug })
const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])
</script>

<template>
  <DataTablePage
    title="Datasets"
    :columns="[
      { id: 'name', header: 'Name' },
      { id: 'valid', header: 'Valid' },
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
    <template #actions>
      <button
        class="aots-btn-secondary disabled:opacity-40"
        :disabled="!selectedIds.length"
        @click="bulk.start('datasets', selectedIds, projectStore.currentProject!.pk)"
      >
        Bulk download
      </button>
    </template>
    <template #cell-name="{ row }">
      <RouterLink :to="`/w/${projectSlug}/analysis/datasets/${row.pk}/`">{{ row.name }}</RouterLink>
    </template>
  </DataTablePage>
</template>
