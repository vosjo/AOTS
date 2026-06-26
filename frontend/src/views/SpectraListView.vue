<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import SpectraSectionNav from '@/components/SpectraSectionNav.vue'
import BulkDownloadProgress from '@/components/BulkDownloadProgress.vue'
import { confirmAction } from '@/composables/useConfirm'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'
import { useSpectraSectionFilters } from '@/composables/useSpectraSectionFilters'
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
  specfiles: { pk: number }[]
  star: { name: string; pk: number } | string
}

const route = useRoute()
const auth = useAuthStore()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const bulk = useBulkDownload()
const filterOpen = ref(false)
const { filters, clearFilters } = useSpectraSectionFilters(
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
  spectraSectionSelection: 'spectra',
})

const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])
const { emptyMessage } = useEmptyTableMessage({ query, filters, entity: 'spectra' })
const anyRaw = computed(() => rows.value.some((r) => selectedIds.value.includes(r.pk) && r.has_raw_files))

async function deleteSelected() {
  if (!(await confirmAction({
    title: 'Delete spectra',
    message: 'Delete selected spectra? This cannot be undone.',
  }))) return
  for (const pk of selectedIds.value) {
    await api(`/api/observations/spectra/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}

function starOf(row: SpectrumRow): { name: string; pk: number } | null {
  return typeof row.star === 'object' && row.star ? row.star : null
}

function starName(row: SpectrumRow) {
  return starOf(row)?.name ?? (typeof row.star === 'string' ? row.star : '—')
}

function formatResolution(value: number) {
  return value >= 0 ? String(Math.round(value)) : '—'
}

function formatAirmass(value: number) {
  return value >= 0 ? value.toFixed(2) : '—'
}
</script>

<template>
  <div class="space-y-4">
    <SpectraSectionNav />

    <DataTablePage
      hide-title
      :columns="[
      { id: 'hjd', header: 'HJD' },
      { id: 'star', header: 'System' },
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
    :empty-message="emptyMessage"
    :selected="selected"
    :selectable="auth.isAuthenticated"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
    @toggle-row="toggleRow"
    @toggle-all="toggleAll(rows)"
  >
    <template #actions>
      <AppButton variant="secondary" @click="filterOpen = true">Filters</AppButton>
      <AppButton
        variant="primary"
        class="inline-flex items-center gap-1.5"
        :to="`/w/${projectSlug}/observations/spectra/upload`"
      >
        <Plus class="w-4 h-4" />
        Upload reduced spectra
      </AppButton>
      <template v-if="auth.isAuthenticated">
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length || bulk.busy"
          @click="bulk.start('processed', selectedIds, projectStore.currentProject!.pk)"
        >
          Download processed
        </AppButton>
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length || !anyRaw || bulk.busy"
          :title="anyRaw ? '' : 'No raw data for selection'"
          @click="bulk.start('raw', selectedIds, projectStore.currentProject!.pk)"
        >
          Download raw
        </AppButton>
        <AppButton
          variant="danger"
          :disabled="!selectedIds.length"
          @click="deleteSelected"
        >
          Delete
        </AppButton>
      </template>
      <BulkDownloadProgress :status="bulk.status" :busy="bulk.busy" />
    </template>

    <template #cell-hjd="{ row }">
      <RouterLink :to="`/w/${projectSlug}/observations/spectra/${row.pk}/`">{{ row.hjd }}</RouterLink>
    </template>
    <template #cell-star="{ row }">
      <AppButton
        v-if="starOf(row)"
        variant="link"
        :to="`/w/${projectSlug}/systems/stars/${starOf(row)!.pk}`"
      >
        {{ starOf(row)!.name }}
      </AppButton>
      <span v-else>{{ starName(row) }}</span>
    </template>
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
  </div>
</template>
