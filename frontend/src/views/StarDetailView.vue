<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import {
  CheckCircle2,
  Copy,
  Download,
  Eye,
  EyeOff,
  Pencil,
  Loader2,
  Plus,
  Trash2,
  XCircle,
} from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import AladinMap from '@/components/AladinMap.vue'
import BokehPlot from '@/components/BokehPlot.vue'
import { api, formatApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

interface TagRef {
  pk: number
  name: string
  color: string
  description?: string
}

interface StarCore {
  pk: number
  name: string
  project: number
  ra: number
  dec: number
  classification: string
  classification_type: string
  classification_type_display: string
  observing_status: string
  observing_status_display: string
  note: string
  tags: TagRef[]
}

interface ParamRow {
  name: string
  display_label: string
  unit: string
  unit_display: string
  provenance?: string
  value?: string
  primary?: string
  secondary?: string
}

interface RelatedStar {
  pk: number
  name: string
  observing_status: string
}

interface StarDetailPayload {
  star: StarCore
  coordinates: {
    ra_hms: string
    dec_dms: string
    ra_deg: string
    dec_deg: string
  }
  related_systems: Array<{
    tag: TagRef
    stars_lower: RelatedStar[]
    stars_upper: RelatedStar[]
    stars_lower_hidden: number
    stars_upper_hidden: number
  }>
  summary_parameters: {
    has_components: boolean
    system: ParamRow[]
    component: ParamRow[]
  }
  observation_counts: {
    photometry: number
    spectra: number
    raw_science: number
    lightcurves: number
  }
  photometry: Array<{
    pk: number
    band: string
    value: string
    error: string
    measurement: number
    error_value: number | null
    unit: string
    wavelength: number
  }>
  spectra: Array<{
    pk: number
    hjd: number
    hjd_date: string
    instrument: string
    telescope: string
    resolution_display: string
    exptime: number
    snr_display: string
    minwave_display: string
    maxwave_display: string
  }>
  raw_spectra: Array<{
    hjd: number
    hjd_date: string
    instrument: string
    filetype: string
    exptime: number
    linked: boolean
  }>
  lightcurves: Array<{
    pk: number
    hjd: number
    hjd_date: string
    passband: string
    exptime: number
    duration: number
  }>
  identifiers: Array<{ pk: number; name: string; href: string }>
  stilism_url: string
}

interface BokehEmbed {
  script: string
  div: string
}

interface AnalysisPlot {
  analysis_id: number
  analysis_name: string
  category: string
  category_label: string
  added_by: string
  added_on: string
  fit: boolean
  note: string
  parameters: {
    system: ParamRow[]
    component: ParamRow[]
  }
  detail_href: string
  embed: BokehEmbed
}

interface ParamOverview {
  components: Array<{
    component: string
    rows: Array<{
      name: string
      display_label?: string
      unit: string
      unit_display?: string
      value: string
      provenance?: string
      other_measurements?: Array<{
        parameter_id: number
        value: string
        provenance: string
      }>
    }>
  }>
}

interface EditableParameter {
  id: number
  name: string
  display_label: string
  component: string
  source: string
  unit: string
  unit_display: string
  value: number
  error: number
}

interface PhotDraftRow {
  band: string
  value: string
  error: string
}

const STATUS_COLORS: Record<string, string> = {
  NE: 'bg-sky-400',
  ON: 'bg-amber-400',
  FI: 'bg-emerald-400',
  RE: 'bg-red-400',
}

const CLASSIFICATION_TYPE_OPTIONS = [
  { value: 'PH', label: 'Photometric' },
  { value: 'SP', label: 'Spectroscopic' },
] as const

const OBSERVING_STATUS_OPTIONS = [
  { value: 'NE', label: 'New' },
  { value: 'ON', label: 'Ongoing' },
  { value: 'FI', label: 'Finished' },
  { value: 'RE', label: 'Rejected' },
] as const

const route = useRoute()
const auth = useAuthStore()
const themeStore = useThemeStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const starId = computed(() => route.params.id as string)

const noteEdit = ref(false)
const noteText = ref('')
const basicDataDialog = ref(false)
const basicDataSaving = ref(false)
const basicDataError = ref('')
const basicDataDraft = ref({
  name: '',
  ra: '',
  dec: '',
  classification: '',
  classification_type: 'PH',
  observing_status: 'NE',
})
const tagDialog = ref(false)
const selectedTags = ref<number[]>([])
const obsExpanded = ref(true)
const paramDialog = ref(false)
const paramSaving = ref(false)
const paramDraft = ref<Record<number, { value: string; error: string }>>({})
const photEdit = ref(false)
const photSaving = ref(false)
const photVizierLoading = ref(false)
const photError = ref<string | null>(null)
const paramGaiaLoading = ref(false)
const paramGaiaMessage = ref<string | null>(null)
const paramGaiaError = ref<string | null>(null)
const tessFetchLoading = ref(false)
const tessFetchMessage = ref<string | null>(null)
const tessFetchError = ref<string | null>(null)
const photDraft = ref<PhotDraftRow[]>([])
const addBandOpen = ref(false)
const copyPhotDialog = ref(false)
const identifierDialog = ref(false)
const newIdentifierName = ref('')
const newIdentifierHref = ref('')
const simbadIdentifiersLoading = ref(false)
const simbadIdentifiersMessage = ref<string | null>(null)
const simbadIdentifiersError = ref<string | null>(null)

const { data: detail, refetch } = useQuery({
  queryKey: computed(() => ['star-detail', starId.value]),
  queryFn: () => api<StarDetailPayload>(`/api/systems/stars/${starId.value}/detail/`),
})

const { data: sed, refetch: refetchSed } = useQuery({
  queryKey: computed(() => ['star-sed', starId.value, themeStore.mode]),
  queryFn: () =>
    api<BokehEmbed>(`/api/systems/stars/${starId.value}/sed/?theme=${themeStore.mode}`),
})

const { data: analysisPlots } = useQuery({
  queryKey: computed(() => ['star-analysis-plots', starId.value, themeStore.mode]),
  queryFn: () =>
    api<{ plots: AnalysisPlot[] }>(
      `/api/systems/stars/${starId.value}/analysis-plots/?theme=${themeStore.mode}`,
    ),
})

const groupedAnalysisPlots = computed(() => {
  const groups = new Map<string, AnalysisPlot[]>()
  for (const plot of analysisPlots.value?.plots ?? []) {
    const key = plot.category_label || plot.category
    const list = groups.get(key) ?? []
    list.push(plot)
    groups.set(key, list)
  }
  return [...groups.entries()].map(([label, plots]) => ({ label, plots }))
})

const { data: tags } = useQuery({
  queryKey: ['tags'],
  queryFn: () => api<{ results: Array<{ pk: number; name: string }> }>('/api/systems/tags/?page_size=500'),
  enabled: tagDialog,
})

const { data: paramOverview, isFetching: paramLoading, refetch: refetchParams } = useQuery({
  queryKey: computed(() => ['star-parameters', starId.value]),
  queryFn: () => api<ParamOverview>(`/api/systems/stars/${starId.value}/parameters/`),
  enabled: computed(() => !!starId.value),
})

const { data: editableParams, refetch: refetchEditableParams } = useQuery({
  queryKey: computed(() => ['star-editable-parameters', starId.value]),
  queryFn: () =>
    api<{ parameters: EditableParameter[] }>(
      `/api/systems/stars/${starId.value}/parameters/editable/`,
    ),
  enabled: computed(() => paramDialog.value && auth.isAuthenticated),
})

const { data: photBandOptions } = useQuery({
  queryKey: computed(() => ['star-photometry-options', starId.value]),
  queryFn: () =>
    api<{
      bands: Array<{ band: string; survey: string }>
      surveys: Array<{ id: string; label: string; bands: string[] }>
    }>(
      `/api/systems/stars/${starId.value}/photometry/options/`,
    ),
  enabled: computed(() => photEdit.value && auth.isAuthenticated),
})

const star = computed(() => detail.value?.star)
const counts = computed(() => detail.value?.observation_counts)

const photometryCsv = computed(() => {
  const rows = detail.value?.photometry ?? []
  const lines = ['band_name, wavelength, mag, err']
  for (const p of rows) {
    lines.push(`${p.band},${p.wavelength},${p.value},${p.error}`)
  }
  return lines.join('\n')
})

const headerTitle = computed(() => {
  const s = star.value
  if (!s) return ''
  return s.classification ? `${s.name} — ${s.classification}` : s.name
})

const availableBandSurveys = computed(() => {
  const used = new Set(photDraft.value.map((r) => r.band))
  return (photBandOptions.value?.surveys ?? [])
    .map((survey) => ({
      ...survey,
      bands: survey.bands.filter((band) => !used.has(band)),
    }))
    .filter((survey) => survey.bands.length > 0)
})


watch(detail, (d) => {
  if (d?.star.note) noteText.value = d.star.note
}, { immediate: true })

function statusDot(status: string) {
  return STATUS_COLORS[status] ?? 'bg-slate-500'
}

async function saveNote() {
  await api(`/api/systems/stars/${starId.value}/`, {
    method: 'PATCH',
    body: { note: noteText.value },
  })
  noteEdit.value = false
  refetch()
}

function parseRaDegrees(value: string): number {
  const v = value.trim()
  if (!v.includes(':')) return Number(v)
  const parts = v.split(':').map((part) => Number(part))
  if (parts.some((part) => Number.isNaN(part))) {
    throw new Error('Invalid right ascension format')
  }
  const hours =
    parts.length === 3
      ? parts[0] + parts[1] / 60 + parts[2] / 3600
      : parts.length === 2
        ? parts[0] + parts[1] / 60
        : NaN
  if (Number.isNaN(hours)) throw new Error('Invalid right ascension format')
  return hours * 15
}

function parseDecDegrees(value: string): number {
  const v = value.trim()
  const sign = v.startsWith('-') ? -1 : 1
  const abs = v.replace(/^[+-]/, '')
  if (!abs.includes(':')) return Number(v)
  const parts = abs.split(':').map((part) => Number(part))
  if (parts.some((part) => Number.isNaN(part))) {
    throw new Error('Invalid declination format')
  }
  const degrees =
    parts.length === 3
      ? Math.abs(parts[0]) + parts[1] / 60 + parts[2] / 3600
      : parts.length === 2
        ? Math.abs(parts[0]) + parts[1] / 60
        : NaN
  if (Number.isNaN(degrees)) throw new Error('Invalid declination format')
  return sign * degrees
}

function openBasicDataEdit() {
  const s = star.value
  const coords = detail.value?.coordinates
  if (!s || !coords) return
  basicDataError.value = ''
  basicDataDraft.value = {
    name: s.name,
    ra: coords.ra_hms,
    dec: coords.dec_dms,
    classification: s.classification ?? '',
    classification_type: s.classification_type || 'PH',
    observing_status: s.observing_status || 'NE',
  }
  basicDataDialog.value = true
}

async function saveBasicData() {
  basicDataSaving.value = true
  basicDataError.value = ''
  try {
    const ra = parseRaDegrees(basicDataDraft.value.ra)
    const dec = parseDecDegrees(basicDataDraft.value.dec)
    if (Number.isNaN(ra) || Number.isNaN(dec)) {
      throw new Error('Coordinates must be valid numbers or h:m:s / °:′:″ values')
    }
    await api(`/api/systems/stars/${starId.value}/`, {
      method: 'PATCH',
      body: {
        name: basicDataDraft.value.name.trim(),
        ra,
        dec,
        classification: basicDataDraft.value.classification,
        classification_type: basicDataDraft.value.classification_type,
        observing_status: basicDataDraft.value.observing_status,
      },
    })
    basicDataDialog.value = false
    await refetch()
  } catch (err) {
    basicDataError.value = formatApiError(err)
  } finally {
    basicDataSaving.value = false
  }
}

async function saveTags() {
  await api(`/api/systems/stars/${starId.value}/`, {
    method: 'PATCH',
    body: { tag_ids: selectedTags.value },
  })
  tagDialog.value = false
  refetch()
}

function openTags() {
  selectedTags.value = (star.value?.tags ?? []).map((t) => t.pk)
  tagDialog.value = true
}

async function addIdentifier() {
  if (!star.value || !newIdentifierName.value.trim()) return
  await api('/api/systems/identifiers/', {
    method: 'POST',
    body: {
      star: star.value.pk,
      project: star.value.project,
      name: newIdentifierName.value.trim(),
      href: newIdentifierHref.value.trim(),
    },
  })
  identifierDialog.value = false
  newIdentifierName.value = ''
  newIdentifierHref.value = ''
  refetch()
}

async function deleteIdentifier(pk: number) {
  await api(`/api/systems/identifiers/${pk}/`, { method: 'DELETE' })
  refetch()
}

async function fetchSimbadIdentifiers() {
  simbadIdentifiersLoading.value = true
  simbadIdentifiersError.value = null
  simbadIdentifiersMessage.value = null
  try {
    const res = await api<{
      status: string
      detail: string
      added?: number
      skipped?: number
      total_simbad?: number
    }>(`/api/systems/stars/${starId.value}/simbad/identifiers/`, {
      method: 'POST',
    })
    simbadIdentifiersMessage.value = res.detail
    await refetch()
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }; message?: string }
    simbadIdentifiersError.value =
      err.data?.detail ?? err.message ?? 'Simbad identifier sync failed'
  } finally {
    simbadIdentifiersLoading.value = false
  }
}

async function copyPhotometry() {
  await navigator.clipboard.writeText(photometryCsv.value)
  copyPhotDialog.value = false
}

function startPhotEdit() {
  photDraft.value = (detail.value?.photometry ?? []).map((p) => ({
    band: p.band,
    value: String(p.measurement),
    error: p.error_value != null ? String(p.error_value) : '',
  }))
  photEdit.value = true
}

function cancelPhotEdit() {
  photEdit.value = false
  photDraft.value = []
  addBandOpen.value = false
}

function addPhotBand(band: string) {
  photDraft.value.push({ band, value: '', error: '' })
  addBandOpen.value = false
}

function removePhotBand(band: string) {
  photDraft.value = photDraft.value.filter((r) => r.band !== band)
}

async function savePhotometry() {
  photSaving.value = true
  try {
    const originalBands = new Set((detail.value?.photometry ?? []).map((p) => p.band))
    const draftBands = new Set(photDraft.value.map((r) => r.band))
    const measurements: Array<{ band: string; value: number | null; error?: number }> = []

    for (const row of photDraft.value) {
      if (row.value.trim() === '') {
        if (originalBands.has(row.band)) {
          measurements.push({ band: row.band, value: null })
        }
        continue
      }
      measurements.push({
        band: row.band,
        value: Number(row.value),
        error: row.error.trim() === '' ? 0 : Number(row.error),
      })
    }
    for (const band of originalBands) {
      if (!draftBands.has(band)) {
        measurements.push({ band, value: null })
      }
    }

    await api(`/api/systems/stars/${starId.value}/photometry/`, {
      method: 'PATCH',
      body: { measurements },
    })
    photEdit.value = false
    await refetch()
  } finally {
    photSaving.value = false
  }
}

async function fetchPhotometryVizier() {
  photVizierLoading.value = true
  photError.value = null
  try {
    await api(`/api/systems/stars/${starId.value}/photometry/from-vizier/`, {
      method: 'POST',
    })
    photEdit.value = false
    await Promise.all([refetch(), refetchSed()])
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }; message?: string }
    photError.value = err.data?.detail ?? err.message ?? 'VizieR fetch failed'
  } finally {
    photVizierLoading.value = false
  }
}

async function fetchGaiaDr3() {
  paramGaiaLoading.value = true
  paramGaiaError.value = null
  paramGaiaMessage.value = null
  try {
    const res = await api<{
      status: string
      detail: string
      warnings?: string[]
    }>(`/api/systems/stars/${starId.value}/gaia/fetch/`, {
      method: 'POST',
    })
    paramGaiaMessage.value = res.detail
    if (res.warnings?.length) {
      paramGaiaMessage.value += ` (${res.warnings.join(' ')})`
    }
    await Promise.all([refetch(), refetchParams(), refetchSed()])
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }; message?: string }
    paramGaiaError.value = err.data?.detail ?? err.message ?? 'Gaia DR3 fetch failed'
  } finally {
    paramGaiaLoading.value = false
  }
}

async function fetchTessLightcurves() {
  tessFetchLoading.value = true
  tessFetchError.value = null
  tessFetchMessage.value = null
  try {
    const res = await api<{
      status: string
      detail: string
      imported?: number[]
      skipped_duplicates?: number
      warnings?: string[]
    }>(`/api/systems/stars/${starId.value}/tess/fetch/`, {
      method: 'POST',
    })
    tessFetchMessage.value = res.detail
    if (res.warnings?.length) {
      tessFetchMessage.value += ` (${res.warnings.join(' ')})`
    }
    await refetch()
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }; message?: string }
    tessFetchError.value = err.data?.detail ?? err.message ?? 'TESS fetch failed'
  } finally {
    tessFetchLoading.value = false
  }
}

const hasParamRows = computed(
  () => (paramOverview.value?.components ?? []).some((comp) => comp.rows.length > 0),
)

async function openParamEditDialog() {
  paramDialog.value = true
  await refetchEditableParams()
}

function closeParamEditDialog() {
  paramDialog.value = false
  paramDraft.value = {}
}

async function saveParameters() {
  paramSaving.value = true
  try {
    const updates = Object.entries(paramDraft.value).map(([id, vals]) => ({
      id: Number(id),
      value: Number(vals.value),
      error: vals.error.trim() === '' ? 0 : Number(vals.error),
    }))
    await api(`/api/systems/stars/${starId.value}/parameters/edit/`, {
      method: 'PATCH',
      body: { updates },
    })
    closeParamEditDialog()
    await Promise.all([refetch(), refetchParams(), refetchEditableParams()])
  } finally {
    paramSaving.value = false
  }
}

watch(editableParams, (data) => {
  if (!paramDialog.value || !data) return
  const draft: Record<number, { value: string; error: string }> = {}
  for (const p of data.parameters) {
    draft[p.id] = { value: String(p.value), error: String(p.error) }
  }
  paramDraft.value = draft
})
</script>

<template>
  <div v-if="detail && star" class="flex gap-4 items-start">
    <aside
      class="hidden xl:block w-52 shrink-0 aots-panel-compact text-xs sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto"
    >
      <h2 class="font-medium text-sm mb-2">Related systems</h2>
      <div class="flex flex-wrap gap-2 mb-3 text-[10px] text-aots-muted">
        <span class="flex items-center gap-1"><i class="inline-block w-2 h-2 rounded-full bg-sky-400" />New</span>
        <span class="flex items-center gap-1"><i class="inline-block w-2 h-2 rounded-full bg-amber-400" />Ongoing</span>
        <span class="flex items-center gap-1"><i class="inline-block w-2 h-2 rounded-full bg-emerald-400" />Finished</span>
        <span class="flex items-center gap-1"><i class="inline-block w-2 h-2 rounded-full bg-red-400" />Rejected</span>
      </div>
      <div v-if="detail.related_systems.length === 0" class="text-aots-muted">
        No related systems found
      </div>
      <div v-for="group in detail.related_systems" :key="group.tag.pk" class="mb-3">
        <h3
          class="font-medium mb-1 border-l-2 pl-1"
          :style="{ borderColor: group.tag.color }"
          :title="group.tag.description"
        >
          {{ group.tag.name }}
        </h3>
        <ul class="space-y-0.5">
          <li v-if="group.stars_lower_hidden" class="text-aots-faint-extra">
            (... {{ group.stars_lower_hidden }} more ...)
          </li>
          <li v-for="s in group.stars_lower" :key="s.pk">
            <RouterLink
              :to="`/w/${projectSlug}/systems/stars/${s.pk}`"
              class="inline-flex items-center gap-1 hover:text-aots-brand"
            >
              <i class="inline-block w-2 h-2 rounded-full shrink-0" :class="statusDot(s.observing_status)" />
              {{ s.name }}
            </RouterLink>
          </li>
          <li>
            <span class="text-aots-brand font-medium">— {{ star.name }} —</span>
          </li>
          <li v-for="s in group.stars_upper" :key="s.pk">
            <RouterLink
              :to="`/w/${projectSlug}/systems/stars/${s.pk}`"
              class="inline-flex items-center gap-1 hover:text-aots-brand"
            >
              <i class="inline-block w-2 h-2 rounded-full shrink-0" :class="statusDot(s.observing_status)" />
              {{ s.name }}
            </RouterLink>
          </li>
          <li v-if="group.stars_upper_hidden" class="text-aots-faint-extra">
            (... {{ group.stars_upper_hidden }} more ...)
          </li>
        </ul>
      </div>
    </aside>

    <div class="flex-1 min-w-0 space-y-3">
      <div class="aots-detail-header">
        <h1 class="text-lg font-semibold m-0">{{ headerTitle }}</h1>
        <span class="inline-flex items-center gap-1.5 text-sm text-aots-muted">
          <i
            class="inline-block w-2 h-2 rounded-full shrink-0"
            :class="statusDot(star.observing_status)"
          />
          {{ star.observing_status_display }}
        </span>
      </div>

      <div class="grid gap-3 lg:grid-cols-2 xl:grid-cols-4">
        <section class="aots-panel-compact">
          <div class="flex justify-between items-center mb-2">
            <h2 class="text-sm font-medium">Basic data</h2>
            <AppButton
              v-if="auth.isAuthenticated"
              variant="icon"
              title="Edit system"
              @click="openBasicDataEdit"
            >
              <Pencil class="w-4 h-4" />
            </AppButton>
          </div>
          <table class="aots-kv-table">
            <tbody>
              <tr><th>Name:</th><td>{{ star.name }}</td></tr>
              <tr>
                <th>Coordinates:</th>
                <td>{{ detail.coordinates.ra_hms }} (h:m:s)</td>
              </tr>
              <tr>
                <th></th>
                <td>{{ detail.coordinates.dec_dms }} (°:′:″)</td>
              </tr>
              <tr>
                <th></th>
                <td>{{ detail.coordinates.ra_deg }} (°)</td>
              </tr>
              <tr>
                <th></th>
                <td>{{ detail.coordinates.dec_deg }} (°)</td>
              </tr>
              <tr><th>Classification:</th><td>{{ star.classification || '—' }}</td></tr>
              <tr><th>Class. type:</th><td>{{ star.classification_type_display || '—' }}</td></tr>
              <tr><th>Observing status:</th><td>{{ star.observing_status_display }}</td></tr>
            </tbody>
          </table>
        </section>

        <section class="aots-panel-compact">
          <div class="flex justify-between items-center mb-2 gap-2">
            <h2 class="text-sm font-medium">Parameters</h2>
            <div v-if="auth.isAuthenticated" class="flex items-center gap-2">
              <AppButton
                variant="secondary"
                size="sm"
                class="inline-flex items-center gap-1"
                :disabled="paramGaiaLoading || paramDialog"
                @click="fetchGaiaDr3"
              >
                <Loader2 v-if="paramGaiaLoading" class="w-3.5 h-3.5 animate-spin" />
                <Download v-else class="w-3.5 h-3.5" />
                {{ paramGaiaLoading ? 'Fetching…' : 'Fetch Gaia DR3' }}
              </AppButton>
              <AppButton
                variant="icon"
                title="Edit parameters"
                @click="openParamEditDialog"
              >
                <Pencil class="w-4 h-4" />
              </AppButton>
            </div>
          </div>

          <AppAlert v-if="paramGaiaError" kind="error" class="mb-2 text-xs">
            {{ paramGaiaError }}
          </AppAlert>
          <AppAlert v-else-if="paramGaiaMessage" kind="info" class="mb-2 text-xs">
            {{ paramGaiaMessage }}
          </AppAlert>

          <p v-if="paramLoading" class="text-xs text-aots-muted">Loading…</p>
          <div v-else-if="paramOverview && hasParamRows" class="max-h-32 overflow-auto">
            <table class="aots-param-table">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="comp in paramOverview.components" :key="comp.component">
                  <tr>
                    <th colspan="2" class="bg-aots-page/60">
                      <b>{{ comp.component }}</b>
                    </th>
                  </tr>
                  <tr v-for="row in comp.rows" :key="`${comp.component}-${row.name}`">
                    <th>
                      {{ row.display_label || row.name }}
                      <span
                        v-if="row.provenance"
                        class="block text-xs font-normal text-aots-muted"
                      >
                        {{ row.provenance }}
                      </span>
                    </th>
                    <td class="font-mono align-top">
                      <div>{{ row.value }}</div>
                      <details
                        v-if="row.other_measurements?.length"
                        class="aots-param-other-measurements mt-1 font-sans"
                      >
                        <summary class="cursor-pointer text-xs text-aots-link">
                          Other measurements ({{ row.other_measurements.length }})
                        </summary>
                        <ul class="mt-1 space-y-1 border-l border-aots-border-subtle pl-2">
                          <li
                            v-for="other in row.other_measurements"
                            :key="other.parameter_id"
                            class="text-xs"
                          >
                            <span class="block text-aots-muted">{{ other.provenance }}</span>
                            <span class="font-mono text-aots-text">{{ other.value }}</span>
                          </li>
                        </ul>
                      </details>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <p v-else class="text-xs text-aots-muted">No parameters</p>
        </section>

        <section class="aots-panel-compact relative">
          <h2 class="text-sm font-medium mb-1">Notes</h2>
          <AppButton
            v-if="auth.isAuthenticated"
            variant="icon"
            class="absolute top-2 right-2"
            title="Edit note"
            @click="noteEdit = !noteEdit"
          >
            <Pencil class="w-4 h-4" />
          </AppButton>
          <p v-if="!noteEdit" class="text-xs text-aots-muted whitespace-pre-wrap pr-8">{{ star.note || '—' }}</p>
          <div v-else class="space-y-2">
            <textarea v-model="noteText" class="aots-field text-xs" rows="4" />
            <AppButton variant="primary" size="sm" @click="saveNote">Save</AppButton>
          </div>
        </section>

        <section v-if="star.ra != null && star.dec != null" class="aots-panel-compact">
          <AladinMap
            compact
            vizier-catalog="I/345"
            :ra="Number(star.ra)"
            :dec="Number(star.dec)"
          />
        </section>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <section class="aots-panel-compact">
          <div class="flex justify-between items-center mb-2 gap-2">
            <h2 class="text-sm font-medium">Aliases</h2>
            <div v-if="auth.isAuthenticated" class="flex items-center gap-2">
              <AppButton
                variant="secondary"
                size="sm"
                class="inline-flex items-center gap-1"
                :disabled="simbadIdentifiersLoading"
                title="Add alternative names from Simbad"
                @click="fetchSimbadIdentifiers"
              >
                <Loader2 v-if="simbadIdentifiersLoading" class="w-3.5 h-3.5 animate-spin" />
                <Download v-else class="w-3.5 h-3.5" />
                {{ simbadIdentifiersLoading ? 'Fetching…' : 'Update from Simbad' }}
              </AppButton>
              <AppButton
                variant="icon"
                title="Add alias"
                @click="identifierDialog = true"
              >
                <Plus class="w-4 h-4" />
              </AppButton>
            </div>
          </div>
          <AppAlert v-if="simbadIdentifiersError" kind="error" class="mb-2 text-xs">
            {{ simbadIdentifiersError }}
          </AppAlert>
          <AppAlert v-else-if="simbadIdentifiersMessage" kind="info" class="mb-2 text-xs">
            {{ simbadIdentifiersMessage }}
          </AppAlert>
          <div
            v-if="detail.identifiers.length"
            class="max-h-20 overflow-y-auto overflow-x-hidden pr-1"
          >
            <div class="flex flex-wrap gap-2 text-xs">
              <div
                v-for="ident in detail.identifiers"
                :key="ident.pk"
                class="inline-flex items-center gap-1 rounded border border-aots px-2 py-1"
              >
                <a v-if="ident.href" :href="ident.href" target="_blank" rel="noopener">{{ ident.name }}</a>
                <span v-else>{{ ident.name }}</span>
                <AppButton
                  v-if="auth.isAuthenticated"
                  variant="icon-danger"
                  @click="deleteIdentifier(ident.pk)"
                >
                  <Trash2 class="w-3 h-3" />
                </AppButton>
              </div>
            </div>
          </div>
          <p v-else class="text-xs text-aots-muted">None known.</p>
        </section>

        <section class="aots-panel-compact">
          <div class="flex justify-between items-center mb-2">
            <h2 class="text-sm font-medium">Tags</h2>
            <AppButton
              v-if="auth.isAuthenticated"
              variant="icon"
              title="Edit tags"
              @click="openTags"
            >
              <Pencil class="w-4 h-4" />
            </AppButton>
          </div>
          <div
            v-if="star.tags.length"
            class="max-h-20 overflow-y-auto overflow-x-hidden pr-1"
          >
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="t in star.tags"
                :key="t.pk"
                class="text-xs px-2 py-0.5 rounded border"
                :style="{ borderColor: t.color }"
              >
                {{ t.name }}
              </span>
            </div>
          </div>
          <p v-else class="text-xs text-aots-muted">No tags</p>
        </section>
      </div>

      <section class="aots-panel-compact">
        <div class="flex items-center gap-2 mb-2">
          <AppButton
            variant="icon"
            :title="obsExpanded ? 'Hide details' : 'Show details'"
            @click="obsExpanded = !obsExpanded"
          >
            <EyeOff v-if="obsExpanded" class="w-4 h-4" />
            <Eye v-else class="w-4 h-4" />
          </AppButton>
          <h2 class="text-sm font-medium">Observations</h2>
        </div>
        <p v-if="!obsExpanded && counts" class="text-xs text-aots-muted">
          Photometric: {{ counts.photometry }},
          Spectra: {{ counts.spectra }},
          Raw science files: {{ counts.raw_science }},
          Light curves: {{ counts.lightcurves }}
        </p>

        <div v-if="obsExpanded" class="space-y-4">
          <p v-if="counts" class="text-xs text-aots-muted">
            Photometric observations: {{ counts.photometry }},
            Reduced spectroscopic observations: {{ counts.spectra }},
            Spectroscopic raw files: {{ counts.raw_science }},
            Light curves: {{ counts.lightcurves }}
          </p>

          <div class="grid gap-3 xl:grid-cols-2">
            <div class="min-w-0">
              <h3 class="text-xs font-medium text-aots-muted mb-2 text-center">SED</h3>
              <div class="min-h-[200px] relative">
                <BokehPlot v-if="sed" compact :script="sed.script" :div="sed.div" />
                <div
                  v-if="photVizierLoading"
                  class="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 rounded bg-aots-page/75"
                >
                  <Loader2 class="w-8 h-8 animate-spin text-aots-link" />
                  <span class="text-xs text-aots-muted">Fetching photometry from VizieR…</span>
                </div>
              </div>
              <p v-if="detail.stilism_url" class="text-xs text-center mt-1">
                <a :href="detail.stilism_url" target="_blank" rel="noopener">
                  Stilism Reddening Map (Lallement+2018)
                </a>
              </p>
            </div>

            <div>
              <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
                <h3 class="text-xs font-medium text-aots-muted">Photometry</h3>
                <div class="flex flex-wrap items-center justify-end gap-2">
                <AppButton
                  v-if="!photEdit && detail.photometry.length"
                  variant="secondary"
                  size="sm"
                  class="inline-flex items-center gap-1"
                  @click="copyPhotDialog = true"
                >
                  <Copy class="w-3.5 h-3.5" />
                  Copy
                </AppButton>
                <AppButton
                  v-if="auth.isAuthenticated"
                  variant="secondary"
                  size="sm"
                  class="inline-flex items-center gap-1"
                  :disabled="photVizierLoading || photEdit"
                  title="Fetches GALEX, SDSS, Pan-STARRS, 2MASS, WISE, APASS, SKYMAP from VizieR (Gaia via Fetch Gaia DR3)"
                  @click="fetchPhotometryVizier"
                >
                  <Loader2 v-if="photVizierLoading" class="w-3.5 h-3.5 animate-spin" />
                  <Download v-else class="w-3.5 h-3.5" />
                  {{ photVizierLoading ? 'Fetching…' : 'Fetch from VizieR' }}
                </AppButton>
                <AppButton
                  v-if="auth.isAuthenticated && !photEdit"
                  variant="secondary"
                  size="sm"
                  class="inline-flex items-center gap-1"
                  @click="startPhotEdit"
                >
                  <Pencil class="w-3.5 h-3.5" />
                  Edit
                </AppButton>
                <template v-if="photEdit">
                  <div class="relative">
                    <AppButton
                      variant="secondary"
                      size="sm"
                      @click="addBandOpen = !addBandOpen"
                    >
                      Add band
                    </AppButton>
                    <div
                      v-if="addBandOpen"
                      class="absolute right-0 z-10 mt-1 max-h-48 overflow-y-auto rounded border border-aots bg-aots-surface py-1 shadow-lg min-w-[10rem]"
                    >
                      <template v-for="survey in availableBandSurveys" :key="survey.id">
                        <div class="px-3 py-1 text-[10px] font-medium text-aots-muted">
                          {{ survey.label }}
                        </div>
                        <button
                          v-for="band in survey.bands"
                          :key="band"
                          type="button"
                          class="block w-full px-3 py-1 text-left text-xs hover:bg-aots-surface-muted"
                          @click="addPhotBand(band)"
                        >
                          {{ band }}
                        </button>
                      </template>
                    </div>
                  </div>
                  <AppButton
                    variant="primary"
                    size="sm"
                    :disabled="photSaving"
                    @click="savePhotometry"
                  >
                    Save
                  </AppButton>
                  <AppButton variant="ghost" size="sm" @click="cancelPhotEdit">
                    Cancel
                  </AppButton>
                </template>
                </div>
              </div>
              <AppAlert v-if="photError" kind="error" class="mb-2">{{ photError }}</AppAlert>
              <div class="overflow-x-auto">
                <table class="aots-obs-table">
                  <thead>
                    <tr>
                      <th>Band</th>
                      <th>Value</th>
                      <th>Error</th>
                      <th v-if="!photEdit">Unit</th>
                      <th v-if="photEdit" />
                    </tr>
                  </thead>
                  <tbody>
                    <template v-if="photEdit">
                      <tr v-for="row in photDraft" :key="row.band">
                        <td>{{ row.band }}</td>
                        <td>
                          <input v-model="row.value" type="number" step="any" class="aots-field-sm w-24" />
                        </td>
                        <td>
                          <input v-model="row.error" type="number" step="any" class="aots-field-sm w-20" />
                        </td>
                        <td>
                          <AppButton
                            variant="icon-danger"
                            title="Remove band"
                            @click="removePhotBand(row.band)"
                          >
                            <Trash2 class="w-3.5 h-3.5" />
                          </AppButton>
                        </td>
                      </tr>
                      <tr v-if="!photDraft.length">
                        <td colspan="4" class="text-aots-muted">Add photometry bands</td>
                      </tr>
                    </template>
                    <template v-else>
                      <tr v-for="p in detail.photometry" :key="p.pk">
                        <td>{{ p.band }}</td>
                        <td>{{ p.value }}</td>
                        <td>{{ p.error }}</td>
                        <td>{{ p.unit }}</td>
                      </tr>
                      <tr v-if="!detail.photometry.length">
                        <td colspan="4" class="text-aots-muted">No photometry values</td>
                      </tr>
                    </template>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div v-if="detail.spectra.length">
            <h3 class="text-xs font-medium text-aots-muted mb-2">Reduced spectra</h3>
            <div class="overflow-x-auto">
              <table class="aots-obs-table">
                <thead>
                  <tr>
                    <th>HJD</th>
                    <th>Date</th>
                    <th>Instrument</th>
                    <th>Resolution</th>
                    <th>Exp time (s)</th>
                    <th>SNR</th>
                    <th>Range (Å)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="spec in detail.spectra" :key="spec.pk">
                    <td>
                      <RouterLink :to="`/w/${projectSlug}/observations/spectra/${spec.pk}/`">
                        {{ spec.hjd.toFixed(3) }}
                      </RouterLink>
                    </td>
                    <td>{{ spec.hjd_date }}</td>
                    <td>{{ spec.instrument }} @ {{ spec.telescope }}</td>
                    <td>{{ spec.resolution_display }}</td>
                    <td>{{ spec.exptime }}</td>
                    <td>{{ spec.snr_display }}</td>
                    <td>{{ spec.minwave_display }} - {{ spec.maxwave_display }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="detail.raw_spectra.length">
            <h3 class="text-xs font-medium text-aots-muted mb-2">Raw spectra</h3>
            <div class="overflow-x-auto">
              <table class="aots-obs-table">
                <thead>
                  <tr>
                    <th>HJD</th>
                    <th>Date</th>
                    <th>Instrument</th>
                    <th>File type</th>
                    <th>Exp time (s)</th>
                    <th>Reduced</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(raw, idx) in detail.raw_spectra" :key="idx">
                    <td>{{ raw.hjd.toFixed(3) }}</td>
                    <td>{{ raw.hjd_date }}</td>
                    <td>{{ raw.instrument }}</td>
                    <td>{{ raw.filetype }}</td>
                    <td>{{ raw.exptime }}</td>
                    <td>
                      <CheckCircle2 v-if="raw.linked" class="w-4 h-4 text-emerald-400 inline" />
                      <XCircle v-else class="w-4 h-4 text-red-400 inline" />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
              <h3 class="text-xs font-medium text-aots-muted">Light curves</h3>
              <AppButton
                v-if="auth.isAuthenticated"
                variant="secondary"
                size="sm"
                class="inline-flex items-center gap-1"
                :disabled="tessFetchLoading"
                title="Download TESS sector light curves from MAST for this system"
                @click="fetchTessLightcurves"
              >
                <Loader2 v-if="tessFetchLoading" class="w-3.5 h-3.5 animate-spin" />
                <Download v-else class="w-3.5 h-3.5" />
                {{ tessFetchLoading ? 'Fetching…' : 'Fetch TESS' }}
              </AppButton>
            </div>
            <AppAlert v-if="tessFetchError" kind="error" class="mb-2 text-xs">
              {{ tessFetchError }}
            </AppAlert>
            <AppAlert v-else-if="tessFetchMessage" kind="info" class="mb-2 text-xs">
              {{ tessFetchMessage }}
            </AppAlert>
            <p v-if="!detail.lightcurves.length" class="text-xs text-aots-muted mb-2">
              No light curves linked to this system yet.
            </p>
            <div v-else class="overflow-x-auto">
              <table class="aots-obs-table">
                <thead>
                  <tr>
                    <th>HJD</th>
                    <th>Date</th>
                    <th>Passband</th>
                    <th>Exptime (s)</th>
                    <th>Duration (h)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="lc in detail.lightcurves" :key="lc.pk">
                    <td>
                      <RouterLink :to="`/w/${projectSlug}/observations/lightcurves/${lc.pk}/`">
                        {{ lc.hjd.toFixed(3) }}
                      </RouterLink>
                    </td>
                    <td>{{ lc.hjd_date }}</td>
                    <td>{{ lc.passband }}</td>
                    <td>{{ lc.exptime }}</td>
                    <td>{{ lc.duration.toFixed(1) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <section
        v-for="group in groupedAnalysisPlots"
        :key="group.label"
        class="space-y-3"
      >
        <h2 class="text-base font-medium text-aots">{{ group.label }}</h2>
        <article
          v-for="plot in group.plots"
          :key="plot.analysis_id"
          class="aots-panel-compact"
        >
          <h3 class="text-sm font-medium mb-2 flex items-center gap-2 flex-wrap">
            <RouterLink :to="`/w/${projectSlug}/analysis/analyses/${plot.analysis_id}/`">
              {{ plot.analysis_name }}
            </RouterLink>
            <CheckCircle2 v-if="plot.fit" class="w-4 h-4 text-emerald-400" title="Fit" />
            <XCircle v-else class="w-4 h-4 text-red-400" title="No fit" />
            <span class="text-xs text-aots-muted">{{ plot.added_by }} · {{ plot.added_on }}</span>
          </h3>
          <div class="grid gap-3 xl:grid-cols-2">
            <div class="min-w-0">
              <BokehPlot compact :script="plot.embed.script" :div="plot.embed.div" />
            </div>
            <div>
              <h4 class="text-xs text-aots-muted mb-1">Parameters</h4>
              <table class="aots-param-table mb-3">
                <thead>
                  <tr>
                    <th>Parameter</th>
                    <th v-if="plot.parameters.component.length">Prim.</th>
                    <th v-if="plot.parameters.component.length">Sec.</th>
                    <th v-else>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in plot.parameters.system" :key="`ds-${plot.analysis_id}-sys-${p.name}`">
                    <th>{{ p.display_label }}</th>
                    <td :colspan="plot.parameters.component.length ? 2 : 1">{{ p.value }}</td>
                  </tr>
                  <tr v-for="p in plot.parameters.component" :key="`ds-${plot.analysis_id}-cmp-${p.name}`">
                    <th>{{ p.display_label }}</th>
                    <td>{{ p.primary }}</td>
                    <td>{{ p.secondary }}</td>
                  </tr>
                </tbody>
              </table>
              <h4 class="text-xs text-aots-muted mb-1">Description</h4>
              <p class="text-xs text-aots-muted whitespace-pre-wrap">{{ plot.note || '—' }}</p>
            </div>
          </div>
        </article>
      </section>
    </div>

    <dialog
      v-if="basicDataDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="basicDataDialog = false"
    >
      <div class="aots-panel w-full max-w-md max-h-[80vh] overflow-y-auto">
        <h3 class="font-medium mb-3">Edit system</h3>
        <div class="space-y-3">
          <label class="block">
            <span class="aots-label">Name</span>
            <input v-model="basicDataDraft.name" type="text" class="aots-field w-full" />
          </label>
          <label class="block">
            <span class="aots-label">Right ascension</span>
            <input
              v-model="basicDataDraft.ra"
              type="text"
              class="aots-field w-full"
              placeholder="h:m:s or degrees"
            />
          </label>
          <label class="block">
            <span class="aots-label">Declination</span>
            <input
              v-model="basicDataDraft.dec"
              type="text"
              class="aots-field w-full"
              placeholder="°:′:″ or degrees"
            />
          </label>
          <label class="block">
            <span class="aots-label">Classification</span>
            <input v-model="basicDataDraft.classification" type="text" class="aots-field w-full" />
          </label>
          <label class="block">
            <span class="aots-label">Classification type</span>
            <select v-model="basicDataDraft.classification_type" class="aots-select w-full">
              <option
                v-for="opt in CLASSIFICATION_TYPE_OPTIONS"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </option>
            </select>
          </label>
          <label class="block">
            <span class="aots-label">Observing status</span>
            <select v-model="basicDataDraft.observing_status" class="aots-select w-full">
              <option
                v-for="opt in OBSERVING_STATUS_OPTIONS"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </option>
            </select>
          </label>
        </div>
        <AppAlert v-if="basicDataError" kind="error" class="mt-3 text-xs">
          {{ basicDataError }}
        </AppAlert>
        <div class="flex gap-2 mt-4">
          <AppButton variant="primary" :disabled="basicDataSaving" @click="saveBasicData">
            Save
          </AppButton>
          <AppButton variant="ghost" @click="basicDataDialog = false">Cancel</AppButton>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="tagDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="tagDialog = false"
    >
      <div class="aots-panel w-full max-w-md max-h-[80vh] overflow-y-auto">
        <h3 class="font-medium mb-3">Edit tags</h3>
        <label v-for="t in tags?.results ?? []" :key="t.pk" class="flex items-center gap-2 text-sm py-1">
          <input v-model="selectedTags" type="checkbox" :value="t.pk" />
          {{ t.name }}
        </label>
        <div class="flex gap-2 mt-4">
          <AppButton variant="primary" @click="saveTags">Save</AppButton>
          <AppButton variant="ghost" @click="tagDialog = false">Cancel</AppButton>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="paramDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="closeParamEditDialog"
    >
      <div class="aots-panel w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="flex flex-wrap justify-between items-center gap-2 mb-3">
          <h3 class="font-medium">Edit parameters</h3>
          <div class="flex flex-wrap items-center gap-2">
            <AppButton
              variant="primary"
              size="sm"
              :disabled="paramSaving"
              @click="saveParameters"
            >
              Save changes
            </AppButton>
            <AppButton variant="ghost" size="sm" @click="closeParamEditDialog">
              Cancel
            </AppButton>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="aots-param-table">
            <thead>
              <tr>
                <th>Parameter</th>
                <th>Component</th>
                <th>Source</th>
                <th>Value</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in editableParams?.parameters ?? []" :key="p.id">
                <th>{{ p.display_label }}</th>
                <td>{{ p.component }}</td>
                <td>{{ p.source }}</td>
                <td v-if="paramDraft[p.id]">
                  <input
                    v-model="paramDraft[p.id].value"
                    type="number"
                    step="any"
                    class="aots-field-sm w-28"
                  />
                </td>
                <td v-if="paramDraft[p.id]">
                  <input
                    v-model="paramDraft[p.id].error"
                    type="number"
                    step="any"
                    class="aots-field-sm w-24"
                  />
                </td>
              </tr>
              <tr v-if="!(editableParams?.parameters.length)">
                <td colspan="5" class="text-aots-muted">No editable parameters</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="copyPhotDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="copyPhotDialog = false"
    >
      <div class="aots-panel w-full max-w-lg">
        <h3 class="font-medium mb-2">Copy photometry</h3>
        <textarea class="aots-field text-xs font-mono" rows="8" readonly :value="photometryCsv" />
        <div class="flex gap-2 mt-3">
          <AppButton variant="primary" @click="copyPhotometry">Copy text</AppButton>
          <AppButton variant="ghost" @click="copyPhotDialog = false">Close</AppButton>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="identifierDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="identifierDialog = false"
    >
      <div class="aots-panel w-full max-w-md space-y-3">
        <h3 class="font-medium">Add an identifier</h3>
        <input v-model="newIdentifierName" class="aots-field" placeholder="New alias" />
        <input v-model="newIdentifierHref" class="aots-field" placeholder="Optional link" />
        <div class="flex gap-2">
          <AppButton variant="primary" @click="addIdentifier">Add</AppButton>
          <AppButton variant="ghost" @click="identifierDialog = false">Cancel</AppButton>
        </div>
      </div>
    </dialog>
  </div>
</template>
