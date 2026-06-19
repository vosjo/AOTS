<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import DataTablePage from '@/components/DataTablePage.vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import SystemsSectionNav from '@/components/SystemsSectionNav.vue'
import BulkDownloadProgress from '@/components/BulkDownloadProgress.vue'
import { saveCarryOver } from '@/composables/useCarryOver'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useGaiaFetch } from '@/composables/useGaiaFetch'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import type { AlertKind } from '@/utils/alertStyles'

interface TagRef {
  pk: number
  name: string
  color: string
  description?: string
}

interface AnalysisBadge {
  name: string
  color: string
  href: string
}

interface StarRow {
  pk: number
  name: string
  ra_hms: string
  dec_dms: string
  classification: string
  classification_type: string
  classification_type_display: string
  observing_status: string
  observing_status_display: string
  nphot: number
  nspec: number
  nlc: number
  analyses: AnalysisBadge[]
  tags: TagRef[]
}

function analysisInitial(name: string) {
  return name.charAt(0) || '?'
}

const STATUS_OPTIONS = [
  { value: 'FI', label: 'Finished' },
  { value: 'ON', label: 'Ongoing' },
  { value: 'RE', label: 'Rejected' },
  { value: 'NE', label: 'New' },
] as const

const TYPE_OPTIONS = [
  { value: 'PH', label: 'Photometric' },
  { value: 'SP', label: 'Spectroscopic' },
] as const

const STATUS_COLORS: Record<string, string> = {
  NE: 'bg-sky-400',
  ON: 'bg-amber-400',
  FI: 'bg-emerald-400',
  RE: 'bg-red-400',
}

const emptyFilters = () => ({
  name: '',
  coordinates: '',
  ra: '',
  dec: '',
  classification: '',
  classification_type: [] as string[],
  status: [] as string[],
  tags: [] as string[],
  mag_min: '',
  mag_max: '',
  nphot_min: '',
  nphot_max: '',
  nspec_min: '',
  nspec_max: '',
  nlc_min: '',
  nlc_max: '',
})

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectStore = useProjectStore()
const gaiaFetch = useGaiaFetch()
const gaiaSummaryMessage = ref('')
const projectSlug = computed(() => route.params.projectSlug as string)
const filterOpen = ref(false)
const filters = ref(emptyFilters())

const { query, page, pageSize, selected, toggleRow, toggleAll, clearSelection } = useDataTablePage<StarRow>({
  endpoint: '/api/systems/stars/',
  projectSlug,
  filters,
})
const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])

const { data: allTags } = useQuery({
  queryKey: computed(() => ['tags', projectStore.currentProject?.pk]),
  queryFn: () =>
    api<{ results: TagRef[] }>(
      `/api/systems/tags/?project=${projectStore.currentProject!.pk}&page_size=500`,
    ),
  enabled: computed(() => !!projectStore.currentProject),
})

const tagDialog = ref(false)
const statusDialog = ref(false)
const addDialog = ref(false)
const selectedTagIds = ref<number[]>([])
const newStatus = ref('')
const statusError = ref('')
const tagError = ref('')
const addError = ref('')
const addErrorKind = ref<AlertKind>('error')
const addBusy = ref(false)
const csvFile = ref<FileList | null>(null)

interface SimbadMatch {
  main_id: string
  ra: string
  dec: string
  classification: string
  classification_type: string
}

interface SimbadResolveResult extends Partial<SimbadMatch> {
  status: 'unique' | 'ambiguous' | 'not_found' | 'empty'
  matches?: SimbadMatch[]
  best_match?: boolean
}

const addForm = ref({
  name: '',
  ra: '',
  dec: '',
  classification: '',
  classification_type: 'PH',
  get_simbad: false,
  tag_ids: [] as number[],
})

const simbadResolving = ref(false)
const simbadMessage = ref('')
const simbadAmbiguous = ref<SimbadMatch[]>([])
let simbadResolveTimer: ReturnType<typeof setTimeout> | undefined

function clearFilters() {
  filters.value = emptyFilters()
}

function toggleFilterArray(key: 'classification_type' | 'status' | 'tags', value: string) {
  const list = filters.value[key]
  const idx = list.indexOf(value)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(value)
}

function statusDot(status: string) {
  return STATUS_COLORS[status] ?? 'bg-slate-500'
}

function carryTo(path: string) {
  saveCarryOver(selectedIds.value)
  router.push(`/w/${projectSlug.value}/observations/${path}/`)
}

async function deleteSelected() {
  if (!confirm('Are you sure you want to delete these Systems? This can NOT be undone!')) return
  for (const pk of selectedIds.value) {
    await api(`/api/systems/stars/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}

async function fetchGaiaSelected() {
  const project = projectStore.currentProject
  if (!project || !selectedIds.value.length) return
  const n = selectedIds.value.length
  if (
    !confirm(
      `Fetch Gaia DR3 data for ${n} system(s)? Existing Gaia DR3 measurements will be replaced.`,
    )
  ) {
    return
  }
  gaiaSummaryMessage.value = ''
  try {
    await gaiaFetch.startBulk(selectedIds.value, project.pk)
    const s = gaiaFetch.lastSummary
    if (s) {
      gaiaSummaryMessage.value = `Gaia DR3 fetch complete: ${s.ok} updated, ${s.no_match} no match, ${s.partial} partial, ${s.failed} failed.`
    }
    await query.refetch()
  } catch (e) {
    gaiaSummaryMessage.value = e instanceof Error ? e.message : 'Gaia DR3 fetch failed'
  }
}

function openTagDialog() {
  selectedTagIds.value = []
  tagError.value = ''
  tagDialog.value = true
}

async function saveTags() {
  tagError.value = ''
  try {
    for (const pk of selectedIds.value) {
      await api(`/api/systems/stars/${pk}/`, {
        method: 'PATCH',
        body: { tag_ids: selectedTagIds.value },
      })
    }
    tagDialog.value = false
    clearSelection()
    await query.refetch()
  } catch (e) {
    tagError.value = e instanceof Error ? e.message : 'Update failed'
  }
}

function openStatusDialog() {
  newStatus.value = ''
  statusError.value = ''
  statusDialog.value = true
}

async function saveStatus() {
  if (!newStatus.value) {
    statusError.value = 'You need to select a status option!'
    return
  }
  statusError.value = ''
  try {
    for (const pk of selectedIds.value) {
      await api(`/api/systems/stars/${pk}/`, {
        method: 'PATCH',
        body: { observing_status: newStatus.value },
      })
    }
    statusDialog.value = false
    clearSelection()
    await query.refetch()
  } catch (e) {
    statusError.value = e instanceof Error ? e.message : 'Update failed'
  }
}

function resetSimbadResolveState() {
  simbadMessage.value = ''
  simbadAmbiguous.value = []
  simbadResolving.value = false
  clearTimeout(simbadResolveTimer)
}

function applySimbadMatch(match: SimbadMatch) {
  addForm.value.ra = match.ra
  addForm.value.dec = match.dec
  addForm.value.classification = match.classification
  addForm.value.classification_type = match.classification_type
  simbadAmbiguous.value = []
}

function selectSimbadMatch(match: SimbadMatch) {
  addForm.value.name = match.main_id
  applySimbadMatch(match)
  simbadMessage.value = `Resolved: ${match.main_id}`
}

async function resolveSimbadName() {
  const name = addForm.value.name.trim()
  if (!name || !addForm.value.get_simbad) return

  simbadResolving.value = true
  simbadMessage.value = ''
  simbadAmbiguous.value = []
  try {
    const res = await api<SimbadResolveResult>(
      `/api/systems/stars/resolve-simbad/?name=${encodeURIComponent(name)}`,
    )
    if (res.status === 'unique' && res.main_id && res.ra && res.dec) {
      applySimbadMatch(res as SimbadMatch)
      simbadMessage.value = res.best_match
        ? `Resolved (best match): ${res.main_id}`
        : `Resolved: ${res.main_id}`
    } else if (res.status === 'ambiguous' && res.matches?.length) {
      simbadAmbiguous.value = res.matches
      simbadMessage.value = 'Multiple Simbad matches — please select one:'
      addForm.value.ra = ''
      addForm.value.dec = ''
      addForm.value.classification = ''
    } else {
      simbadMessage.value = 'No unique Simbad match found.'
      addForm.value.ra = ''
      addForm.value.dec = ''
      addForm.value.classification = ''
    }
  } catch (e) {
    simbadMessage.value = e instanceof Error ? e.message : 'Simbad lookup failed'
  } finally {
    simbadResolving.value = false
  }
}

function scheduleSimbadResolve() {
  clearTimeout(simbadResolveTimer)
  if (!addForm.value.get_simbad) return
  simbadResolveTimer = setTimeout(resolveSimbadName, 600)
}

watch(
  () => addForm.value.get_simbad,
  (useSimbad) => {
    if (!useSimbad) {
      resetSimbadResolveState()
      return
    }
    scheduleSimbadResolve()
  },
)

watch(
  () => addForm.value.name,
  () => {
    if (!addForm.value.get_simbad) return
    scheduleSimbadResolve()
  },
)

function openAddDialog() {
  addForm.value = {
    name: '',
    ra: '',
    dec: '',
    classification: '',
    classification_type: 'PH',
    get_simbad: false,
    tag_ids: [],
  }
  csvFile.value = null
  addError.value = ''
  addErrorKind.value = 'error'
  resetSimbadResolveState()
  addDialog.value = true
}

function toggleAddTag(pk: number) {
  const idx = addForm.value.tag_ids.indexOf(pk)
  if (idx >= 0) addForm.value.tag_ids.splice(idx, 1)
  else addForm.value.tag_ids.push(pk)
}

async function uploadCsv() {
  if (!csvFile.value?.length || !projectStore.currentProject) return
  addBusy.value = true
  addError.value = ''
  addErrorKind.value = 'error'
  const fd = new FormData()
  fd.append('project', String(projectStore.currentProject.pk))
  for (const f of csvFile.value) fd.append('system', f)
  try {
    const res = await api<string>('/api/systems/stars/bulk-upload/', { method: 'POST', body: fd })
    addError.value = typeof res === 'string' ? res : 'Upload complete.'
    addErrorKind.value = 'success'
    await query.refetch()
  } catch (e) {
    addError.value = e instanceof Error ? e.message : String(e)
    addErrorKind.value = 'error'
  } finally {
    addBusy.value = false
  }
}

async function addSystem() {
  if (!projectStore.currentProject) return
  addBusy.value = true
  addError.value = ''
  addErrorKind.value = 'error'
  try {
    await api('/api/systems/stars/create-from-form/', {
      method: 'POST',
      body: {
        project: projectStore.currentProject.pk,
        name: addForm.value.name,
        ra: addForm.value.ra,
        dec: addForm.value.dec,
        classification: addForm.value.classification,
        classification_type: addForm.value.classification_type,
        get_simbad: addForm.value.get_simbad,
        tag_ids: addForm.value.tag_ids,
      },
    })
    addDialog.value = false
    await query.refetch()
  } catch (e) {
    addError.value = e instanceof Error ? e.message : String(e)
  } finally {
    addBusy.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <SystemsSectionNav />

    <AppAlert v-if="gaiaSummaryMessage" kind="info">{{ gaiaSummaryMessage }}</AppAlert>

    <DataTablePage
      hide-title
    :columns="[
      { id: 'name', header: 'Name' },
      { id: 'ra_hms', header: 'RA' },
      { id: 'dec_dms', header: 'Dec' },
      { id: 'classification', header: 'Type' },
      { id: 'nphot', header: 'Phot' },
      { id: 'nspec', header: 'Spec' },
      { id: 'nlc', header: 'LC' },
      { id: 'analyses', header: 'Analyses' },
      { id: 'tags', header: 'Tags' },
      { id: 'observing_status', header: 'Status' },
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
        @click="openAddDialog"
      >
        <Plus class="w-4 h-4" />
        Add system(s)
      </AppButton>
      <template v-if="auth.isAuthenticated">
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length"
          @click="openTagDialog"
        >
          Edit tags
        </AppButton>
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length"
          @click="openStatusDialog"
        >
          Change status
        </AppButton>
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length || gaiaFetch.busy"
          @click="fetchGaiaSelected"
        >
          Fetch Gaia DR3
        </AppButton>
        <BulkDownloadProgress :status="gaiaFetch.status" :busy="gaiaFetch.busy" />
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length"
          @click="carryTo('spectra')"
        >
          Carry-over → Spectra
        </AppButton>
        <AppButton
          variant="secondary"
          :disabled="!selectedIds.length"
          @click="carryTo('lightcurves')"
        >
          Carry-over → LC
        </AppButton>
        <AppButton
          variant="danger"
          :disabled="!selectedIds.length"
          @click="deleteSelected"
        >
          Delete
        </AppButton>
      </template>
    </template>

    <template #cell-name="{ row }">
      <RouterLink :to="`/w/${projectSlug}/systems/stars/${row.pk}`">{{ row.name }}</RouterLink>
    </template>

    <template #cell-classification="{ row }">
      <span
        :class="`classification-${row.classification_type}`"
        :title="row.classification_type_display"
      >
        {{ row.classification || '—' }}
      </span>
    </template>

    <template #cell-analyses="{ row }">
      <span v-if="!row.analyses?.length" class="text-aots-faint-extra">—</span>
      <RouterLink
        v-for="(item, index) in row.analyses"
        :key="`${row.pk}-${index}-${item.href}`"
        :to="item.href"
        class="aots-analysis-badge"
        :style="{ backgroundColor: item.color }"
        :title="item.name"
      >
        {{ analysisInitial(item.name) }}
      </RouterLink>
    </template>

    <template #cell-tags="{ row }">
      <span v-if="!row.tags?.length" class="text-aots-faint-extra">—</span>
      <span
        v-for="tag in row.tags"
        :key="tag.pk"
        class="aots-tag-chip"
        :style="{ borderColor: tag.color }"
        :title="tag.description"
      >
        {{ tag.name }}
      </span>
    </template>

    <template #cell-observing_status="{ row }">
      <span
        class="inline-flex items-center gap-1.5"
        :title="row.observing_status_display"
      >
        <i
          class="inline-block w-2 h-2 rounded-full shrink-0"
          :class="statusDot(row.observing_status)"
        />
        <span class="text-xs text-aots-muted">{{ row.observing_status_display }}</span>
      </span>
    </template>
  </DataTablePage>

  <ListFilterPanel
    :open="filterOpen"
    @close="filterOpen = false"
    @clear="clearFilters(); query.refetch()"
    @apply="filterOpen = false; query.refetch()"
  >
    <input v-model="filters.name" placeholder="Name (Simbad resolver)" class="aots-field" />
    <input
      v-model="filters.coordinates"
      placeholder="Coordinates (ra -- dec)"
      class="aots-field"
      title="00:00:00 +00:00:00 or 000.000 +00.000"
    />
    <input v-model="filters.ra" placeholder="RA min -- max" class="aots-field" />
    <input v-model="filters.dec" placeholder="Dec min -- max" class="aots-field" />
    <input v-model="filters.classification" placeholder="Type / class string" class="aots-field" />
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.mag_min" placeholder="G-mag min" class="aots-field-sm" />
      <input v-model="filters.mag_max" placeholder="G-mag max" class="aots-field-sm" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.nphot_min" placeholder="#phot min" class="aots-field-sm" />
      <input v-model="filters.nphot_max" placeholder="#phot max" class="aots-field-sm" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.nspec_min" placeholder="#spec min" class="aots-field-sm" />
      <input v-model="filters.nspec_max" placeholder="#spec max" class="aots-field-sm" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <input v-model="filters.nlc_min" placeholder="#lc min" class="aots-field-sm" />
      <input v-model="filters.nlc_max" placeholder="#lc max" class="aots-field-sm" />
    </div>

    <div class="space-y-1">
      <p class="text-xs text-aots-muted">Type</p>
      <label
        v-for="opt in TYPE_OPTIONS"
        :key="opt.value"
        class="flex items-center gap-2 text-sm"
      >
        <input
          type="checkbox"
          :checked="filters.classification_type.includes(opt.value)"
          @change="toggleFilterArray('classification_type', opt.value)"
        />
        {{ opt.label }}
      </label>
    </div>

    <div class="space-y-1">
      <p class="text-xs text-aots-muted">Status</p>
      <label
        v-for="opt in STATUS_OPTIONS"
        :key="opt.value"
        class="flex items-center gap-2 text-sm"
      >
        <input
          type="checkbox"
          :checked="filters.status.includes(opt.value)"
          @change="toggleFilterArray('status', opt.value)"
        />
        {{ opt.label }}
      </label>
    </div>

    <div v-if="allTags?.results?.length" class="space-y-1">
      <p class="text-xs text-aots-muted">Tags</p>
      <label
        v-for="tag in allTags.results"
        :key="tag.pk"
        class="flex items-center gap-2 text-sm"
      >
        <input
          type="checkbox"
          :checked="filters.tags.includes(String(tag.pk))"
          @change="toggleFilterArray('tags', String(tag.pk))"
        />
        {{ tag.name }}
      </label>
    </div>
  </ListFilterPanel>

  <dialog
    v-if="tagDialog"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    @click.self="tagDialog = false"
  >
    <div class="aots-panel w-full max-w-sm">
      <h3 class="font-medium mb-3">Add/remove tags</h3>
      <ul class="space-y-1 text-sm max-h-60 overflow-y-auto">
        <li v-for="tag in allTags?.results ?? []" :key="tag.pk">
          <label class="flex items-center gap-2">
            <input v-model="selectedTagIds" type="checkbox" :value="tag.pk" />
            {{ tag.name }}
          </label>
        </li>
      </ul>
      <AppAlert v-if="tagError" kind="error" class="mt-2">{{ tagError }}</AppAlert>
      <div class="flex gap-2 mt-4">
        <AppButton variant="primary" @click="saveTags">Update</AppButton>
        <AppButton variant="ghost" @click="tagDialog = false">Cancel</AppButton>
      </div>
    </div>
  </dialog>

  <dialog
    v-if="statusDialog"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    @click.self="statusDialog = false"
  >
    <div class="aots-panel w-full max-w-xs">
      <h3 class="font-medium mb-3">Change status</h3>
      <ul class="space-y-2 text-sm">
        <li v-for="opt in STATUS_OPTIONS" :key="opt.value">
          <label class="flex items-center gap-2">
            <input v-model="newStatus" type="radio" :value="opt.value" />
            {{ opt.label }}
          </label>
        </li>
      </ul>
      <AppAlert v-if="statusError" kind="error" class="mt-2">{{ statusError }}</AppAlert>
      <div class="flex gap-2 mt-4">
        <AppButton variant="primary" @click="saveStatus">Update</AppButton>
        <AppButton variant="ghost" @click="statusDialog = false">Cancel</AppButton>
      </div>
    </div>
  </dialog>

  <dialog
    v-if="addDialog"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    @click.self="addDialog = false"
  >
    <div class="aots-panel w-full max-w-2xl max-h-[90vh] overflow-y-auto space-y-6">
      <div class="flex items-center justify-between gap-4">
        <h3 class="font-medium">Add system(s)</h3>
        <AppButton variant="ghost" class="shrink-0" @click="addDialog = false">Close</AppButton>
      </div>

      <section class="space-y-3">
        <h4 class="text-sm font-medium text-aots-muted">Bulk upload (.csv)</h4>
        <input type="file" accept=".csv" class="aots-field w-full" @change="(e) => csvFile = (e.target as HTMLInputElement).files" />
        <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
          <AppButton
            variant="secondary"
            :disabled="addBusy || !csvFile?.length"
            @click="uploadCsv"
          >
            Upload .csv file
          </AppButton>
          <AppButton
            variant="link"
            size="sm"
            href="/media/docs/Bulk_system_example.csv"
            target="_blank"
            rel="noopener"
          >
            Example .csv file
          </AppButton>
        </div>
      </section>

      <section class="space-y-3 border-t border-aots pt-4">
        <h4 class="text-sm font-medium text-aots-muted">Single system</h4>
        <label class="flex items-center gap-2">
          <input v-model="addForm.get_simbad" type="checkbox" />
          <span>Use Simbad (coordinates and spectral classification are filled automatically)</span>
        </label>
        <div class="grid sm:grid-cols-2 gap-3">
          <label class="block sm:col-span-2">
            <span class="aots-label">Name (main id) *</span>
            <div class="flex gap-2">
              <input
                v-model="addForm.name"
                type="text"
                class="aots-field w-full"
                @blur="addForm.get_simbad && resolveSimbadName()"
              />
              <AppButton
                v-if="addForm.get_simbad"
                variant="secondary"
                class="shrink-0"
                :disabled="simbadResolving || !addForm.name.trim()"
                @click="resolveSimbadName"
              >
                {{ simbadResolving ? 'Resolving…' : 'Resolve' }}
              </AppButton>
            </div>
          </label>
          <AppAlert
            v-if="addForm.get_simbad && (simbadMessage || simbadResolving)"
            :kind="simbadAmbiguous.length ? 'warning' : 'info'"
            class="sm:col-span-2"
          >
            <template v-if="simbadResolving">Looking up name in Simbad…</template>
            <template v-else>{{ simbadMessage }}</template>
          </AppAlert>
          <ul
            v-if="addForm.get_simbad && simbadAmbiguous.length"
            class="sm:col-span-2 space-y-1 max-h-40 overflow-y-auto rounded border border-aots p-2 text-sm"
          >
            <li v-for="match in simbadAmbiguous" :key="match.main_id">
              <button
                type="button"
                class="w-full text-left rounded px-2 py-1 hover:bg-aots-surface-muted/60"
                @click="selectSimbadMatch(match)"
              >
                <span class="font-medium">{{ match.main_id }}</span>
                <span class="text-aots-muted ml-2">{{ match.ra }}, {{ match.dec }}</span>
                <span v-if="match.classification" class="text-aots-muted ml-2">{{ match.classification }}</span>
              </button>
            </li>
          </ul>
          <label class="block">
            <span class="aots-label">Right ascension{{ addForm.get_simbad ? '' : ' *' }}</span>
            <input
              v-model="addForm.ra"
              type="text"
              class="aots-field w-full"
              :readonly="addForm.get_simbad"
            />
          </label>
          <label class="block">
            <span class="aots-label">Declination{{ addForm.get_simbad ? '' : ' *' }}</span>
            <input
              v-model="addForm.dec"
              type="text"
              class="aots-field w-full"
              :readonly="addForm.get_simbad"
            />
          </label>
          <label class="block">
            <span class="aots-label">Spectral classification</span>
            <input
              v-model="addForm.classification"
              type="text"
              class="aots-field w-full"
              :readonly="addForm.get_simbad"
            />
          </label>
          <label class="block">
            <span class="aots-label">Classification type</span>
            <select v-model="addForm.classification_type" class="aots-select w-full" :disabled="addForm.get_simbad">
              <option value="PH">Photometric</option>
              <option value="SP">Spectroscopic</option>
            </select>
          </label>
        </div>
        <div v-if="allTags?.results?.length" class="space-y-1">
          <p class="aots-label">Tags</p>
          <label
            v-for="tag in allTags.results"
            :key="tag.pk"
            class="flex items-center gap-2 text-sm"
          >
            <input
              type="checkbox"
              :checked="addForm.tag_ids.includes(tag.pk)"
              @change="toggleAddTag(tag.pk)"
            />
            {{ tag.name }}
          </label>
        </div>
        <AppButton
          variant="primary"
          :disabled="addBusy || !addForm.name || (addForm.get_simbad && simbadAmbiguous.length > 0)"
          @click="addSystem"
        >
          Add system
        </AppButton>
      </section>

      <AppAlert v-if="addError" :kind="addErrorKind" class="whitespace-pre-wrap">{{ addError }}</AppAlert>
    </div>
  </dialog>
  </div>
</template>
