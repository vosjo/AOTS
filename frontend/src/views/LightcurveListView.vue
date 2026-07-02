<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Plus, Trash2 } from '@lucide/vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import BulkDownloadProgress from '@/components/BulkDownloadProgress.vue'
import { confirmAction } from '@/composables/useConfirm'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'
import { useListFilters } from '@/composables/useListFilters'
import { api, formatApiError } from '@/api/client'
import {
  extractUploadDetail,
  parseUploadFeedback,
  type UploadFeedbackItem,
} from '@/utils/uploadFeedback'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useProjectPermissions } from '@/composables/useProjectPermissions'

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
  can_delete?: boolean
}

const route = useRoute()
const auth = useAuthStore()
const { canAdd } = useProjectPermissions()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const bulk = useBulkDownload()
const filterOpen = ref(false)
const uploadOpen = ref(false)
const uploadFiles = ref<FileList | null>(null)
const uploadBusy = ref(false)
const uploading = ref(false)
const uploadFeedback = ref<UploadFeedbackItem[]>([])
const actionError = ref('')
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
  if (canAdd.value) cols.push({ id: 'actions', header: 'Action' })
  return cols
})

function starOf(row: LcRow): StarBrief | null {
  return typeof row.star === 'object' && row.star ? row.star : null
}

function formatLcValue(value: number) {
  return value >= 0 ? String(value) : '—'
}

async function deleteSelected() {
  if (!(await confirmAction({
    title: 'Delete light curves',
    message: 'Are you sure you want to delete these light curves? This cannot be undone!',
  }))) return
  actionError.value = ''
  try {
    for (const pk of selectedIds.value) {
      await api(`/api/observations/lightcurves/${pk}/`, { method: 'DELETE' })
    }
    clearSelection()
    await query.refetch()
  } catch (e) {
    actionError.value = formatApiError(e)
  }
}

async function deleteRow(pk: number) {
  if (!(await confirmAction({
    title: 'Delete light curve',
    message: 'Are you sure you want to delete this light curve? This cannot be undone.',
  }))) return
  actionError.value = ''
  try {
    await api(`/api/observations/lightcurves/${pk}/`, { method: 'DELETE' })
    await query.refetch()
  } catch (e) {
    actionError.value = formatApiError(e)
  }
}

function openUploadDialog() {
  uploadOpen.value = true
  uploadFeedback.value = []
  uploading.value = false
}

function onUploadFilesChange(event: Event) {
  uploadFiles.value = (event.target as HTMLInputElement).files
  uploadFeedback.value = []
}

async function uploadLightCurves() {
  if (!uploadFiles.value?.length || !projectStore.currentProject) return
  uploadBusy.value = true
  uploading.value = true
  uploadFeedback.value = []
  const fd = new FormData()
  fd.append('project', String(projectStore.currentProject.pk))
  for (const f of uploadFiles.value) fd.append('lcfile', f)
  try {
    const res = await api<{ detail?: string } | string>('/api/observations/api-lc-upload/', {
      method: 'POST',
      body: fd,
    })
    const feedback = parseUploadFeedback(extractUploadDetail(res))
    if (feedback.length && feedback.every((item) => item.kind === 'success')) {
      uploadOpen.value = false
      uploadFiles.value = null
      await query.refetch()
      return
    }
    uploadFeedback.value = feedback.length
      ? feedback
      : [{ kind: 'success', title: 'Upload complete', detail: 'All light curves were imported.' }]
  } catch (e) {
    uploadFeedback.value = parseUploadFeedback(formatApiError(e))
  } finally {
    uploadBusy.value = false
    uploading.value = false
  }
}
</script>

<template>
  <AppAlert v-if="actionError" kind="error" class="mb-4">{{ actionError }}</AppAlert>

  <DataTablePage
    title="Light curves"
    :columns="columns"
    :rows="rows"
    :count="query.data.value?.count ?? 0"
    :page="page"
    :page-size="pageSize"
    :loading="query.isLoading.value"
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
        v-if="canAdd"
        variant="primary"
        class="inline-flex items-center gap-1.5"
        @click="openUploadDialog"
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
        v-if="canAdd"
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

    <template v-if="canAdd" #cell-actions="{ row }">
      <AppButton
        v-if="row.can_delete"
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
      <p v-if="uploading" class="mt-3 text-sm text-aots-muted">Uploading and processing files…</p>

      <div v-if="uploadFeedback.length" class="mt-3 space-y-3">
        <AppAlert
          v-for="(item, index) in uploadFeedback"
          :key="index"
          :kind="item.kind"
          :title="item.title"
        >
          <p v-if="item.filename" class="font-mono text-xs break-all opacity-90">
            {{ item.filename }}
          </p>
          <p v-if="item.detail" class="leading-relaxed opacity-90 whitespace-pre-wrap">
            {{ item.detail }}
          </p>
        </AppAlert>
      </div>

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
