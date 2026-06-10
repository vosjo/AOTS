<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import DataTablePage from '@/components/DataTablePage.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useListFilters } from '@/composables/useListFilters'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

interface SpectrumRow {
  pk: number
  hjd: number
  instrument: string
  resolution: number
  airmass: number
  exptime: number
  has_raw_files: boolean
  star: { name: string; pk: number } | string
}

const route = useRoute()
const auth = useAuthStore()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const bulk = useBulkDownload()
const filterOpen = ref(false)
const { filters, clearFilters } = useListFilters(
  {
    target: '',
    telescope: '',
    instrument: '',
    hjd_min: '',
    hjd_max: '',
    exptime_min: '',
    exptime_max: '',
    resolution_min: '',
    resolution_max: '',
    airmass_min: '',
    airmass_max: '',
    fluxcal: '',
  },
  { carryOver: true },
)

const { query, page, pageSize, selected, toggleRow, toggleAll, clearSelection } = useDataTablePage<SpectrumRow>({
  endpoint: '/api/observations/spectra/',
  projectSlug,
  filters,
})

const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])
const anyRaw = computed(() => rows.value.some((r) => selectedIds.value.includes(r.pk) && r.has_raw_files))

async function deleteSelected() {
  if (!confirm('Delete selected spectra? This cannot be undone.')) return
  for (const pk of selectedIds.value) {
    await api(`/api/observations/spectra/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}

function starName(row: SpectrumRow) {
  return typeof row.star === 'object' ? row.star.name : row.star
}

function formatResolution(value: number) {
  return value >= 0 ? String(Math.round(value)) : '—'
}

function formatAirmass(value: number) {
  return value >= 0 ? value.toFixed(2) : '—'
}
</script>

<template>
  <DataTablePage
    title="Spectra"
    :columns="[
      { id: 'hjd', header: 'HJD' },
      { id: 'star', header: 'Target' },
      { id: 'instrument', header: 'Instrument' },
      { id: 'resolution', header: 'Resolution' },
      { id: 'airmass', header: 'Airmass' },
      { id: 'exptime', header: 'Exptime' },
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
      <button class="aots-btn-secondary" @click="filterOpen = true">Filters</button>
      <RouterLink :to="`/w/${projectSlug}/observations/spectra/upload`" class="aots-btn-secondary">Upload</RouterLink>
      <template v-if="auth.isAuthenticated">
        <button
          class="aots-btn-secondary disabled:opacity-40"
          :disabled="!selectedIds.length || bulk.busy"
          @click="bulk.start('processed', selectedIds, projectStore.currentProject!.pk)"
        >
          Download processed
        </button>
        <button
          class="aots-btn-secondary disabled:opacity-40"
          :disabled="!selectedIds.length || !anyRaw || bulk.busy"
          :title="anyRaw ? '' : 'No raw data for selection'"
          @click="bulk.start('raw', selectedIds, projectStore.currentProject!.pk)"
        >
          Download raw
        </button>
        <button
          class="aots-btn-danger disabled:opacity-40"
          :disabled="!selectedIds.length"
          @click="deleteSelected"
        >
          Delete
        </button>
      </template>
      <span v-if="bulk.status" class="text-xs text-slate-400">{{ bulk.status }}</span>
    </template>

    <template #cell-hjd="{ row }">
      <RouterLink :to="`/w/${projectSlug}/observations/spectra/${row.pk}/`">{{ row.hjd }}</RouterLink>
    </template>
    <template #cell-star="{ row }">{{ starName(row) }}</template>
    <template #cell-resolution="{ row }">{{ formatResolution(row.resolution) }}</template>
    <template #cell-airmass="{ row }">{{ formatAirmass(row.airmass) }}</template>
  </DataTablePage>

  <ListFilterPanel
    :open="filterOpen"
    @close="filterOpen = false"
    @clear="clearFilters(); query.refetch()"
    @apply="filterOpen = false; query.refetch()"
  >
    <input v-model="filters.target" placeholder="Target" class="aots-field" />
    <input v-model="filters.telescope" placeholder="Telescope" class="aots-field" />
    <input v-model="filters.instrument" placeholder="Instrument" class="aots-field" />
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.hjd_min" placeholder="HJD min" class="aots-field-sm" />
      <input v-model="filters.hjd_max" placeholder="HJD max" class="aots-field-sm" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.exptime_min" placeholder="Exptime min" class="aots-field-sm" />
      <input v-model="filters.exptime_max" placeholder="Exptime max" class="aots-field-sm" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.resolution_min" placeholder="Resolution min" class="aots-field-sm" />
      <input v-model="filters.resolution_max" placeholder="Resolution max" class="aots-field-sm" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.airmass_min" placeholder="Airmass min" class="aots-field-sm" />
      <input v-model="filters.airmass_max" placeholder="Airmass max" class="aots-field-sm" />
    </div>
    <select v-model="filters.fluxcal" class="aots-select">
      <option value="">Flux calibration: any</option>
      <option value="true">Flux calibration: yes</option>
      <option value="false">Flux calibration: no</option>
    </select>
  </ListFilterPanel>
</template>
