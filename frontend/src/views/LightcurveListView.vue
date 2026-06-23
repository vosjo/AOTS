<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Plus, Trash2 } from '@lucide/vue'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import BulkDownloadProgress from '@/components/BulkDownloadProgress.vue'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'
import { useListFilters } from '@/composables/useListFilters'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

interface StarBrief {
  pk: number
  name: string
  ra: number
  dec: number
}

interface LcRow {
  pk: number
  hjd: number
  instrument: string
  telescope: string
  exptime: number
  cadence: number
  star: StarBrief | string
}

const route = useRoute()
const auth = useAuthStore()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const bulk = useBulkDownload()
const filterOpen = ref(false)
const uploadOpen = ref(false)
const uploadFiles = ref<FileList | null>(null)
const uploadBusy = ref(false)
const uploadStatus = ref('')
const { filters, clearFilters } = useListFilters(
  {
    target: '',
    telescope: '',
    instrument: '',
    hjd_min: '',
    hjd_max: '',
    exptime_min: '',
    exptime_max: '',
  },
  { carryOver: true },
)

const { query, page, pageSize, selected, toggleRow, toggleAll, clearSelection } = useDataTablePage<LcRow>({
  endpoint: '/api/observations/lightcurves/',
  projectSlug,
  filters,
})
const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])

const { emptyMessage } = useEmptyTableMessage({
  query,
  filters,
  entity: 'light curves',
})

const columns = computed(() => {
  const cols = [
    { id: 'hjd', header: 'HJD' },
    { id: 'star', header: 'System' },
    { id: 'instrument', header: 'Instrument' },
    { id: 'exptime', header: 'Exposure time' },
    { id: 'cadence', header: 'Cadence' },
  ]
  if (auth.isAuthenticated) cols.push({ id: 'actions', header: 'Action' })
  return cols
})

function starOf(row: LcRow): StarBrief | null {
  return typeof row.star === 'object' && row.star ? row.star : null
}

function formatLcValue(value: number) {
  return value >= 0 ? String(value) : '—'
}

async function deleteSelected() {
  if (!confirm('Are you sure you want to delete these lightcuves? This can NOT be undone!')) return
  for (const pk of selectedIds.value) {
    await api(`/api/observations/lightcurves/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}

async function deleteRow(pk: number) {
  if (!confirm('Are you sure you want to delete this light curve? This can NOT be undone.')) return
  await api(`/api/observations/lightcurves/${pk}/`, { method: 'DELETE' })
  await query.refetch()
}

function onUploadFilesChange(event: Event) {
  uploadFiles.value = (event.target as HTMLInputElement).files
}

async function uploadLightCurves() {
  if (!uploadFiles.value?.length || !projectStore.currentProject) return
  uploadBusy.value = true
  uploadStatus.value = 'Uploading…'
  const fd = new FormData()
  fd.append('project', String(projectStore.currentProject.pk))
  for (const f of uploadFiles.value) fd.append('lcfile', f)
  try {
    const res = await api<string>('/api/observations/api-lc-upload/', { method: 'POST', body: fd })
    uploadStatus.value = typeof res === 'string' ? res : 'Done.'
    uploadOpen.value = false
    uploadFiles.value = null
    await query.refetch()
  } catch (e) {
    uploadStatus.value = e instanceof Error ? e.message : String(e)
  } finally {
    uploadBusy.value = false
  }
}
</script>

<template>
  <DataTablePage
    title="Light curves"
    :columns="columns"
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
        v-if="auth.isAuthenticated"
        variant="primary"
        class="inline-flex items-center gap-1.5"
        @click="uploadOpen = true"
      >
        <Plus class="w-4 h-4" />
        Upload lightcurve(s)
      </AppButton>
      <AppButton
        variant="secondary"
        :disabled="!selectedIds.length || bulk.busy"
        @click="bulk.start('lightcurves', selectedIds, projectStore.currentProject!.pk)"
      >
        Download selected
      </AppButton>
      <AppButton
        v-if="auth.isAuthenticated"
        variant="danger"
        :disabled="!selectedIds.length"
        @click="deleteSelected"
      >
        Delete selected
      </AppButton>
      <BulkDownloadProgress :status="bulk.status" :busy="bulk.busy" />
    </template>

    <template #cell-hjd="{ row }">
      <RouterLink :to="`/w/${projectSlug}/observations/lightcurves/${row.pk}/`">{{ row.hjd }}</RouterLink>
    </template>

    <template #cell-star="{ row }">
      <template v-if="starOf(row)">
        <AppButton
          variant="link"
          :to="`/w/${projectSlug}/systems/stars/${starOf(row)!.pk}`"
        >
          {{ starOf(row)!.name }}
        </AppButton>
        <span class="text-aots-muted">
          ({{ starOf(row)!.ra.toFixed(5) }} {{ starOf(row)!.dec.toFixed(5) }})
        </span>
      </template>
      <span v-else class="text-aots-muted">—</span>
    </template>

    <template #cell-instrument="{ row }">
      {{ row.instrument }}<template v-if="row.telescope"> @ {{ row.telescope }}</template>
    </template>

    <template #cell-exptime="{ row }">{{ formatLcValue(row.exptime) }}</template>
    <template #cell-cadence="{ row }">{{ formatLcValue(row.cadence) }}</template>

    <template v-if="auth.isAuthenticated" #cell-actions="{ row }">
      <AppButton
        variant="icon-danger"
        title="Delete light curve"
        @click="deleteRow(row.pk)"
      >
        <Trash2 class="w-4 h-4" />
      </AppButton>
    </template>
  </DataTablePage>

  <ListFilterPanel
    :open="filterOpen"
    @close="filterOpen = false"
    @clear="clearFilters(); query.refetch()"
    @apply="filterOpen = false; query.refetch()"
  >
    <input v-model="filters.target" placeholder="Target" class="aots-field" />
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.hjd_min" placeholder="HJD min" class="aots-field-sm" />
      <input v-model="filters.hjd_max" placeholder="HJD max" class="aots-field-sm" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.exptime_min" placeholder="Exptime min" class="aots-field-sm" />
      <input v-model="filters.exptime_max" placeholder="Exptime max" class="aots-field-sm" />
    </div>
    <input v-model="filters.instrument" placeholder="Instrument" class="aots-field" />
    <input v-model="filters.telescope" placeholder="Telescope" class="aots-field" />
  </ListFilterPanel>

  <dialog
    v-if="uploadOpen"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    @click.self="uploadOpen = false"
  >
    <div class="aots-panel w-full max-w-md">
      <h3 class="font-medium mb-4">Add new light curve(s)</h3>
      <fieldset class="space-y-3">
        <legend class="text-sm text-aots-muted mb-2">Select light curve files</legend>
        <input type="file" multiple class="aots-field w-full" @change="onUploadFilesChange" />
      </fieldset>
      <p v-if="uploadStatus" class="mt-3 text-sm text-aots-muted whitespace-pre-wrap">{{ uploadStatus }}</p>
      <div class="flex gap-2 mt-4">
        <AppButton
          variant="primary"
          :disabled="uploadBusy || !uploadFiles?.length"
          @click="uploadLightCurves"
        >
          Upload
        </AppButton>
        <AppButton variant="ghost" :disabled="uploadBusy" @click="uploadOpen = false">
          Cancel
        </AppButton>
      </div>
    </div>
  </dialog>
</template>
