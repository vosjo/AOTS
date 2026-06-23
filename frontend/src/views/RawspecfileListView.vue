<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { CheckCircle2, Plus, XCircle } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import DataTablePage from '@/components/DataTablePage.vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import SpectraSectionNav from '@/components/SpectraSectionNav.vue'
import { api } from '@/api/client'
import BulkDownloadProgress from '@/components/BulkDownloadProgress.vue'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useSpectraSectionFilters } from '@/composables/useSpectraSectionFilters'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

interface RawSpecfileRow {
  pk: number
  hjd: number
  obs_date: string
  instrument: string
  filetype: string
  exptime: number
  filename: string
  added_on: string
  specfile: number[]
  spectra: number[]
  systems: Record<string, string>
}

interface StarOption {
  pk: number
  name: string
}

interface SpecfileOption {
  pk: number
  label: string
}

interface UploadMessage {
  ok: boolean
  text: string
}

const route = useRoute()
const auth = useAuthStore()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const bulk = useBulkDownload()
const filterOpen = ref(false)

const { filters, clearFilters } = useSpectraSectionFilters({
  systems: '',
  instrument: '',
  filename: '',
  filetype: '',
  obs_date: '',
  hjd_min: '',
  hjd_max: '',
  expo_min: '',
  expo_max: '',
})

const { query, page, pageSize, selected, toggleRow, toggleAll, clearSelection } =
  useDataTablePage<RawSpecfileRow>({
    endpoint: '/api/observations/rawspecfiles/',
    projectSlug,
    filters,
    spectraSectionSelection: 'rawspecfiles',
  })

const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])

const uploadOpen = ref(false)
const uploadMode = ref<'choose' | 'simple' | 'manual'>('choose')
const uploadFiles = ref<FileList | null>(null)
const uploadBusy = ref(false)
const uploadMessages = ref<UploadMessage[]>([])

const linkageOpen = ref(false)
const linkageError = ref('')
const linkageBusy = ref(false)
const linkageSystemFilter = ref('')
const linkageSpecfileFilter = ref('')
const linkageSystemIds = ref<number[]>([])
const linkageSpecfileIds = ref<number[]>([])

const uploadSystemFilter = ref('')
const uploadSpecfileFilter = ref('')
const uploadSystemIds = ref<number[]>([])
const uploadSpecfileIds = ref<number[]>([])

const projectPk = computed(() => projectStore.currentProject?.pk)

const { data: starsData } = useQuery({
  queryKey: computed(() => ['stars', projectPk.value, 'rawspec-upload']),
  queryFn: () =>
    api<{ results: StarOption[] }>(
      `/api/systems/stars/?project=${projectPk.value}&page_size=500&ordering=name`,
    ),
  enabled: computed(() => !!projectPk.value && (uploadOpen.value || linkageOpen.value)),
})

const { data: specfilesData } = useQuery({
  queryKey: computed(() => ['specfiles', projectPk.value, 'rawspec-upload']),
  queryFn: () =>
    api<{ results: { pk: number; hjd: number; instrument: string; obs_date?: string }[] }>(
      `/api/observations/specfiles/?project=${projectPk.value}&page_size=500&ordering=-hjd`,
    ),
  enabled: computed(() => !!projectPk.value && (uploadOpen.value || linkageOpen.value)),
})

const allStars = computed(() => starsData.value?.results ?? [])

const allSpecfileOptions = computed<SpecfileOption[]>(() =>
  (specfilesData.value?.results ?? []).map((row) => ({
    pk: row.pk,
    label: `${row.obs_date || row.hjd} — ${row.instrument}`,
  })),
)

const filteredStars = computed(() => {
  const q = linkageOpen.value ? linkageSystemFilter.value : uploadSystemFilter.value
  const needle = q.trim().toLowerCase()
  if (!needle) return allStars.value
  return allStars.value.filter((star) => star.name.toLowerCase().includes(needle))
})

const filteredSpecfiles = computed(() => {
  const q = linkageOpen.value ? linkageSpecfileFilter.value : uploadSpecfileFilter.value
  const needle = q.trim().toLowerCase()
  if (!needle) return allSpecfileOptions.value
  return allSpecfileOptions.value.filter((row) => row.label.toLowerCase().includes(needle))
})

function idFromPath(path: string, segment: string) {
  const m = path.match(new RegExp(`${segment}/(\\d+)`))
  return m ? Number(m[1]) : null
}

function systemsOf(row: RawSpecfileRow) {
  return Object.entries(row.systems ?? {}).map(([name, href]) => ({
    name,
    pk: idFromPath(String(href), 'stars'),
  }))
}

function formatExptime(value: number) {
  return value >= 0 ? String(value) : '—'
}

function isReduced(row: RawSpecfileRow) {
  return (row.specfile?.length ?? 0) > 0
}

function resetUploadDialog() {
  uploadMode.value = 'choose'
  uploadFiles.value = null
  uploadSystemIds.value = []
  uploadSpecfileIds.value = []
  uploadSystemFilter.value = ''
  uploadSpecfileFilter.value = ''
  uploadMessages.value = []
}

function openUploadDialog() {
  resetUploadDialog()
  uploadOpen.value = true
}

function resetLinkageDialog() {
  linkageSystemIds.value = []
  linkageSpecfileIds.value = []
  linkageSystemFilter.value = ''
  linkageSpecfileFilter.value = ''
  linkageError.value = ''
}

function openLinkageDialog() {
  if (!selectedIds.value.length) return
  resetLinkageDialog()
  linkageOpen.value = true
}

function toggleId(list: number[], pk: number) {
  const idx = list.indexOf(pk)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(pk)
}

async function loadSpecfilesForStars(starPks: number[]) {
  const options = new Map<number, string>()
  for (const pk of starPks) {
    const data = await api<Record<string, string>>(`/api/systems/stars/${pk}/specfiles/`)
    for (const [spfPk, label] of Object.entries(data)) {
      options.set(Number(spfPk), label)
    }
  }
  return [...options.entries()].map(([pk, label]) => ({ pk, label }))
}

watch(uploadSystemIds, async (ids) => {
  if (!uploadOpen.value || uploadMode.value !== 'manual' || !ids.length) return
  const options = await loadSpecfilesForStars(ids)
  uploadSpecfileIds.value = uploadSpecfileIds.value.filter((pk) => options.some((o) => o.pk === pk))
})

watch(linkageSystemIds, async (ids) => {
  if (!linkageOpen.value || !ids.length) return
  const options = await loadSpecfilesForStars(ids)
  linkageSpecfileIds.value = linkageSpecfileIds.value.filter((pk) => options.some((o) => o.pk === pk))
})

function appendMulti(fd: FormData, key: string, ids: number[]) {
  for (const id of ids) fd.append(key, String(id))
}

async function uploadRawFiles(simple: boolean) {
  if (!uploadFiles.value?.length || !projectStore.currentProject) return
  uploadBusy.value = true
  uploadMessages.value = []
  const fd = new FormData()
  for (const f of uploadFiles.value) fd.append('raw_files', f)
  if (!simple) {
    appendMulti(fd, 'system', uploadSystemIds.value)
    appendMulti(fd, 'specfile', uploadSpecfileIds.value)
    if (uploadSystemFilter.value.trim()) fd.append('system_name', uploadSystemFilter.value.trim())
    if (uploadSpecfileFilter.value.trim()) fd.append('specfile_date', uploadSpecfileFilter.value.trim())
  }
  try {
    const res = await api<{ messages?: [boolean, string][] }>(
      `/w/${projectSlug.value}/observations/rawspecfiles/`,
      { method: 'POST', body: fd },
    )
    uploadMessages.value = (res.messages ?? []).map(([ok, text]) => ({ ok, text }))
    if (uploadMessages.value.every((m) => m.ok)) {
      uploadOpen.value = false
      resetUploadDialog()
    }
    await query.refetch()
  } catch (e) {
    uploadMessages.value = [{ ok: false, text: e instanceof Error ? e.message : String(e) }]
  } finally {
    uploadBusy.value = false
  }
}

async function deleteSelected() {
  if (!confirm('Are you sure you want to delete this spectrum? This can NOT be undone!')) return
  for (const pk of selectedIds.value) {
    await api(`/api/observations/rawspecfiles/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}

async function updateLinkage() {
  linkageError.value = ''
  if (!linkageSystemIds.value.length && !linkageSpecfileIds.value.length) {
    linkageError.value = 'You need to select a spectrum file or a system!'
    return
  }
  linkageBusy.value = true
  try {
    const body = {
      star: linkageSystemIds.value,
      specfile: linkageSpecfileIds.value,
    }
    for (const pk of selectedIds.value) {
      await api(`/api/observations/rawspecfiles/${pk}/`, { method: 'PATCH', body })
    }
    linkageOpen.value = false
    clearSelection()
    await query.refetch()
  } catch (e) {
    linkageError.value = e instanceof Error ? e.message : 'Update failed'
  } finally {
    linkageBusy.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <SpectraSectionNav />

    <div v-if="uploadMessages.length && !uploadOpen" class="space-y-2">
      <AppAlert
        v-for="(msg, index) in uploadMessages"
        :key="index"
        :kind="msg.ok ? 'success' : 'error'"
      >
        {{ msg.text }}
      </AppAlert>
    </div>

    <DataTablePage
      hide-title
      :columns="[
        { id: 'obs_date', header: 'Observation date' },
        { id: 'instrument', header: 'Instrument' },
        { id: 'filetype', header: 'File type' },
        { id: 'exptime', header: 'Exposure time' },
        { id: 'filename', header: 'File name' },
        { id: 'added_on', header: 'Added on' },
        { id: 'specfile', header: 'Reduced' },
        { id: 'systems', header: 'Systems' },
      ]"
      :rows="rows"
      :count="query.data.value?.count ?? 0"
      :page="page"
      :page-size="pageSize"
      :loading="query.isFetching.value"
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
          @click="openUploadDialog"
        >
          <Plus class="w-4 h-4" />
          Upload raw spectra
        </AppButton>
        <template v-if="auth.isAuthenticated">
          <AppButton
            variant="secondary"
            :disabled="!selectedIds.length"
            @click="openLinkageDialog"
          >
            Update file allocations
          </AppButton>
          <AppButton
            variant="danger"
            :disabled="!selectedIds.length"
            @click="deleteSelected"
          >
            Delete raw data
          </AppButton>
        </template>
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length || bulk.busy"
          @click="bulk.start('rawspecfiles', selectedIds, projectStore.currentProject!.pk)"
        >
          Download raw data
        </AppButton>
        <BulkDownloadProgress :status="bulk.status" :busy="bulk.busy" />
      </template>

      <template #cell-exptime="{ row }">{{ formatExptime(row.exptime) }}</template>

      <template #cell-filename="{ row }">
        <span class="font-mono text-sm break-all">{{ row.filename }}</span>
      </template>

      <template #cell-specfile="{ row }">
        <CheckCircle2
          v-if="isReduced(row)"
          class="w-5 h-5 text-emerald-400"
          title="Allocated to a reduced spectrum."
        />
        <XCircle
          v-else
          class="w-5 h-5 text-red-400"
          title="Not allocated to a reduced spectrum."
        />
      </template>

      <template #cell-systems="{ row }">
        <template v-if="systemsOf(row).length">
          <template v-for="(system, index) in systemsOf(row)" :key="system.name">
            <AppButton
              v-if="system.pk"
              variant="link"
              :to="`/w/${projectSlug}/systems/stars/${system.pk}`"
            >
              {{ system.name }}
            </AppButton>
            <span v-else>{{ system.name }}</span>
            <span v-if="index < systemsOf(row).length - 1">, </span>
          </template>
        </template>
        <span v-else class="text-aots-muted">—</span>
      </template>
    </DataTablePage>
  </div>

  <ListFilterPanel
    :open="filterOpen"
    @close="filterOpen = false"
    @clear="clearFilters(); query.refetch()"
    @apply="filterOpen = false; query.refetch()"
  >
    <input v-model="filters.systems" placeholder="System" class="aots-field" />
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.hjd_min" placeholder="HJD min" class="aots-field-sm" />
      <input v-model="filters.hjd_max" placeholder="HJD max" class="aots-field-sm" />
    </div>
    <input v-model="filters.obs_date" placeholder="Observation date (yyyy-mm-dd)" class="aots-field" />
    <input v-model="filters.instrument" placeholder="Instrument" class="aots-field" />
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.expo_min" placeholder="Exptime min" class="aots-field-sm" />
      <input v-model="filters.expo_max" placeholder="Exptime max" class="aots-field-sm" />
    </div>
    <input v-model="filters.filetype" placeholder="Filetype" class="aots-field" />
    <input v-model="filters.filename" placeholder="Filename" class="aots-field" />
  </ListFilterPanel>

  <dialog
    v-if="uploadOpen"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    @click.self="uploadOpen = false"
  >
    <div class="aots-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto space-y-4">
      <div class="flex items-center justify-between gap-4">
        <h3 class="font-medium">Add raw data</h3>
        <AppButton variant="ghost" class="shrink-0" @click="uploadOpen = false">Close</AppButton>
      </div>

      <template v-if="uploadMode === 'choose'">
        <section class="space-y-3 rounded border border-aots p-4">
          <h4 class="font-medium text-sm">Coherent dataset upload</h4>
          <p class="text-sm text-aots-muted">
            Upload coherent datasets such as an observation night with multiple targets and
            calibration data. Calibration files are associated with all observed objects.
          </p>
          <AppButton variant="secondary" @click="uploadMode = 'simple'">
            Automatically upload coherent data sets
          </AppButton>
        </section>
        <section class="space-y-3 rounded border border-aots p-4">
          <h4 class="font-medium text-sm">Individual data upload</h4>
          <p class="text-sm text-aots-muted">
            Upload individual raw files or bulk data with manual association to systems and/or
            reduced spectra.
          </p>
          <AppButton variant="secondary" @click="uploadMode = 'manual'">
            Manually control how data gets uploaded
          </AppButton>
        </section>
      </template>

      <template v-else>
        <AppButton variant="ghost" size="sm" @click="uploadMode = 'choose'">← Back</AppButton>

        <fieldset v-if="uploadMode === 'manual'" class="space-y-4">
          <legend class="text-sm font-medium text-aots-muted mb-2">Filter systems and spectra</legend>
          <div class="grid sm:grid-cols-2 gap-3">
            <label class="block">
              <span class="aots-label">System name (main id)</span>
              <input v-model="uploadSystemFilter" type="text" class="aots-field w-full" />
            </label>
            <label class="block">
              <span class="aots-label">Observation date</span>
              <input v-model="uploadSpecfileFilter" type="text" class="aots-field w-full" />
            </label>
          </div>
        </fieldset>

        <fieldset v-if="uploadMode === 'manual'" class="space-y-3">
          <legend class="text-sm font-medium text-aots-muted mb-2">
            Allocate raw data to system(s) or reduced spectra
          </legend>
          <div class="grid sm:grid-cols-2 gap-4">
            <div>
              <p class="aots-label mb-1">Systems</p>
              <div class="max-h-40 overflow-y-auto rounded border border-aots p-2 space-y-1">
                <label
                  v-for="star in filteredStars"
                  :key="star.pk"
                  class="flex items-center gap-2 text-sm"
                >
                  <input
                    type="checkbox"
                    :checked="uploadSystemIds.includes(star.pk)"
                    @change="toggleId(uploadSystemIds, star.pk)"
                  />
                  {{ star.name }}
                </label>
              </div>
            </div>
            <div>
              <p class="aots-label mb-1">Reduced spectra (obs. date — instrument)</p>
              <div class="max-h-40 overflow-y-auto rounded border border-aots p-2 space-y-1">
                <label
                  v-for="spf in filteredSpecfiles"
                  :key="spf.pk"
                  class="flex items-center gap-2 text-sm"
                >
                  <input
                    type="checkbox"
                    :checked="uploadSpecfileIds.includes(spf.pk)"
                    @change="toggleId(uploadSpecfileIds, spf.pk)"
                  />
                  {{ spf.label }}
                </label>
              </div>
            </div>
          </div>
        </fieldset>

        <fieldset class="space-y-2">
          <legend class="text-sm font-medium text-aots-muted mb-2">Select raw data</legend>
          <input type="file" multiple class="aots-field w-full" @change="(e) => uploadFiles = (e.target as HTMLInputElement).files" />
        </fieldset>

        <div v-if="uploadMessages.length" class="space-y-2">
          <AppAlert
            v-for="(msg, index) in uploadMessages"
            :key="index"
            :kind="msg.ok ? 'success' : 'error'"
          >
            {{ msg.text }}
          </AppAlert>
        </div>

        <AppButton
          variant="primary"
          :disabled="uploadBusy || !uploadFiles?.length"
          @click="uploadRawFiles(uploadMode === 'simple')"
        >
          Upload raw data
        </AppButton>
      </template>
    </div>
  </dialog>

  <dialog
    v-if="linkageOpen"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    @click.self="linkageOpen = false"
  >
    <div class="aots-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto space-y-4">
      <div class="flex items-center justify-between gap-4">
        <h3 class="font-medium">Adjust file allocations</h3>
        <AppButton variant="ghost" class="shrink-0" @click="linkageOpen = false">Close</AppButton>
      </div>

      <fieldset class="space-y-4">
        <legend class="text-sm font-medium text-aots-muted mb-2">Filter systems and spectra</legend>
        <div class="grid sm:grid-cols-2 gap-3">
          <label class="block">
            <span class="aots-label">System name (main id)</span>
            <input v-model="linkageSystemFilter" type="text" class="aots-field w-full" />
          </label>
          <label class="block">
            <span class="aots-label">Observation date</span>
            <input v-model="linkageSpecfileFilter" type="text" class="aots-field w-full" />
          </label>
        </div>
      </fieldset>

      <fieldset class="space-y-3">
        <legend class="text-sm font-medium text-aots-muted mb-2">
          Select system(s) or reduced spectra for {{ selectedIds.length }} file(s)
        </legend>
        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <p class="aots-label mb-1">Systems</p>
            <div class="max-h-48 overflow-y-auto rounded border border-aots p-2 space-y-1">
              <label
                v-for="star in filteredStars"
                :key="star.pk"
                class="flex items-center gap-2 text-sm"
              >
                <input
                  type="checkbox"
                  :checked="linkageSystemIds.includes(star.pk)"
                  @change="toggleId(linkageSystemIds, star.pk)"
                />
                {{ star.name }}
              </label>
            </div>
          </div>
          <div>
            <p class="aots-label mb-1">Reduced spectra</p>
            <div class="max-h-48 overflow-y-auto rounded border border-aots p-2 space-y-1">
              <label
                v-for="spf in filteredSpecfiles"
                :key="spf.pk"
                class="flex items-center gap-2 text-sm"
              >
                <input
                  type="checkbox"
                  :checked="linkageSpecfileIds.includes(spf.pk)"
                  @change="toggleId(linkageSpecfileIds, spf.pk)"
                />
                {{ spf.label }}
              </label>
            </div>
          </div>
        </div>
      </fieldset>

      <AppAlert v-if="linkageError" kind="error">{{ linkageError }}</AppAlert>

      <AppButton
        variant="primary"
        :disabled="linkageBusy"
        @click="updateLinkage"
      >
        Update
      </AppButton>
    </div>
  </dialog>
</template>
