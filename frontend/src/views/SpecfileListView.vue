<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import SpectraSectionNav from '@/components/SpectraSectionNav.vue'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useSpectraSectionFilters } from '@/composables/useSpectraSectionFilters'

interface SpectrumInfo {
  pk: number
  hjd: number
  target: string
  instrument: string
}

interface SpecfileRow {
  pk: number
  hjd: number
  instrument: string
  filetype: string
  filename: string
  added_on: string
  star: Record<string, string> | string
  spectrum: string
  spectrum_info: SpectrumInfo | null
  rawspecfiles: number[]
}

const route = useRoute()
const projectSlug = computed(() => route.params.projectSlug as string)
const filterOpen = ref(false)
const { filters, clearFilters } = useSpectraSectionFilters({
  target: '',
  instrument: '',
  filename: '',
  filetype: '',
  hjd_min: '',
  hjd_max: '',
})

const { query, page, pageSize, selected, toggleRow, toggleAll } = useDataTablePage<SpecfileRow>({
  endpoint: '/api/observations/specfiles/',
  projectSlug,
  filters,
  spectraSectionSelection: 'specfiles',
})
const rows = computed(() => query.data.value?.results ?? [])

function idFromPath(path: string, segment: string) {
  const m = path.match(new RegExp(`${segment}/(\\d+)`))
  return m ? Number(m[1]) : null
}

function starOf(row: SpecfileRow): { pk: number; name: string } | null {
  if (!row.star) return null
  if (typeof row.star === 'string') {
    return row.star ? { pk: 0, name: row.star } : null
  }
  const entries = Object.entries(row.star)
  if (!entries.length) return null
  const [name, href] = entries[0]
  const pk = idFromPath(String(href), 'stars')
  return pk ? { pk, name } : { pk: 0, name }
}

function isProcessed(row: SpecfileRow) {
  return Boolean(row.spectrum_info ?? row.spectrum)
}

function spectrumLabel(info: SpectrumInfo) {
  const parts: string[] = []
  if (info.target) parts.push(info.target)
  parts.push(String(info.hjd))
  if (info.instrument) parts.push(info.instrument)
  return parts.join(' · ')
}
</script>

<template>
  <div class="space-y-4">
    <SpectraSectionNav />

    <DataTablePage
      hide-title
      :columns="[
      { id: 'hjd', header: 'HJD' },
      { id: 'instrument', header: 'Instrument' },
      { id: 'filetype', header: 'Filetype' },
      { id: 'filename', header: 'Filename' },
      { id: 'added_on', header: 'Added on' },
      { id: 'star', header: 'System' },
      { id: 'spectrum_info', header: 'Spectrum' },
      { id: 'spectrum', header: 'Processed' },
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
      <AppButton variant="secondary" @click="filterOpen = true">Filters</AppButton>
    </template>

    <template #cell-hjd="{ row }">{{ row.hjd }}</template>

    <template #cell-filename="{ row }">
      <span class="font-mono text-sm break-all">{{ row.filename }}</span>
    </template>

    <template #cell-star="{ row }">
      <AppButton
        v-if="starOf(row)?.pk"
        variant="link"
        :to="`/w/${projectSlug}/systems/stars/${starOf(row)!.pk}`"
      >
        {{ starOf(row)!.name }}
      </AppButton>
      <span v-else-if="starOf(row)?.name">{{ starOf(row)!.name }}</span>
      <span v-else class="text-slate-400">—</span>
    </template>

    <template #cell-spectrum_info="{ row }">
      <AppButton
        v-if="row.spectrum_info"
        variant="link"
        :to="`/w/${projectSlug}/observations/spectra/${row.spectrum_info.pk}/`"
      >
        {{ spectrumLabel(row.spectrum_info) }}
      </AppButton>
      <span v-else class="text-slate-400">—</span>
    </template>

    <template #cell-spectrum="{ row }">
      <span :class="isProcessed(row) ? 'text-slate-200' : 'text-slate-400'">
        {{ isProcessed(row) ? 'Yes' : 'No' }}
      </span>
    </template>
  </DataTablePage>

  <ListFilterPanel
    :open="filterOpen"
    @close="filterOpen = false"
    @clear="clearFilters(); query.refetch()"
    @apply="filterOpen = false; query.refetch()"
  >
    <input v-model="filters.target" placeholder="Target" class="aots-field" />
    <input v-model="filters.instrument" placeholder="Instrument" class="aots-field" />
    <input v-model="filters.filename" placeholder="Filename" class="aots-field" />
    <input v-model="filters.filetype" placeholder="Filetype" class="aots-field" />
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.hjd_min" placeholder="HJD min" class="aots-field-sm" />
      <input v-model="filters.hjd_max" placeholder="HJD max" class="aots-field-sm" />
    </div>
  </ListFilterPanel>
  </div>
</template>
