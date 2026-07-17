<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { BookOpen, Download, Pencil, Star, Trash2 } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { confirmAction } from '@/composables/useConfirm'
import { useThemeStore } from '@/stores/theme'

interface StarRef {
  pk: number
  name: string
}

interface CategoryOption {
  value: string
  label: string
  color: string
}

interface AnalysisParameter {
  pk: number
  cname: string
  display_label: string
  unit: string
  unit_display: string
  rvalue: number
  rerror: number
  valid: boolean
}

interface RelatedAnalysis {
  pk: number
  name: string
  category_label: string
  is_current: boolean
}

interface RelatedByCategory {
  pk: number
  star_name: string
  name: string
  is_current: boolean
}

interface FitOption {
  id: string
  label: string
  is_best_fit: boolean
  method: string
  external_id?: string
  uploaded_by?: { pk: number; username: string } | null
  uploaded_on?: string
  can_edit?: boolean
  can_delete?: boolean
}

interface FitParameter {
  cname: string
  display_label: string
  value: number
  error_l: number
  error_u: number
  unit_display: string
}

interface DisplayedParameter {
  key: string
  display_label: string
  value: number
  error: number
  valid: boolean | null
  parameterPk?: number
}

interface RvFitOption {
  id: string
  label: string
  is_best_fit: boolean
  method: string
}

interface ObservationRef {
  pk: number
  hjd: number
  instrument: string
  telescope: string
  passband?: string
}

interface AnalysisDetail {
  pk: number
  name: string
  note: string
  reference: string
  reference_url: string
  fit: boolean
  added_on: string
  added_by: string
  last_modified: string
  modified_by: string
  star: StarRef | Record<string, never>
  category: string
  category_label: string
  category_color: string
  category_source: string
  file_type: string
  parameters: AnalysisParameter[]
  derived_parameters: AnalysisParameter[]
  has_derived_definitions: boolean
  can_edit: boolean
  can_delete: boolean
  file_url: string
  datafile: string
  related_analyses: RelatedAnalysis[]
  related_by_category: RelatedByCategory[]
  rv_fits: RvFitOption[]
  fits: FitOption[]
  can_set_best_fit: boolean
  spectrum: ObservationRef | null
  lightcurve: ObservationRef | null
}

import type { BokehEmbed } from '@/types/bokeh'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const canEdit = computed(() => analysis.value?.can_edit === true)
const canDelete = computed(() => analysis.value?.can_delete === true)
const themeStore = useThemeStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const pk = computed(() => route.params.id as string)

const noteEdit = ref(false)
const noteText = ref('')
const detailsEdit = ref(false)
const nameText = ref('')
const categoryValue = ref('')
const fitValue = ref(true)
const deriveBusy = ref(false)
const deriveMessage = ref('')
const selectedRvFitId = ref('')
const selectedFitId = ref('')
const fitParams = ref<FitParameter[]>([])
const fitActionBusy = ref(false)
const fitFileInput = ref<HTMLInputElement | null>(null)

const displayFits = computed(() => {
  const fits = analysis.value?.fits ?? []
  if (fits.length) return fits
  return (analysis.value?.rv_fits ?? []).map((f) => ({
    ...f,
    uploaded_by: null,
    can_edit: false,
    can_delete: false,
  }))
})

const { data: analysis, refetch } = useQuery({
  queryKey: computed(() => ['analysis', pk.value]),
  queryFn: () => api<AnalysisDetail>(`/api/analysis/analyses/${pk.value}/`),
})

const { data: plots } = useQuery({
  queryKey: computed(() => ['analysis-plots', pk.value, themeStore.mode, selectedFitId.value]),
  queryFn: () => {
    const params = new URLSearchParams({ theme: themeStore.mode })
    const fitId = selectedFitId.value
    if (fitId) params.set('fit_id', fitId)
    return api<Record<string, BokehEmbed>>(
      `/api/analysis/analyses/${pk.value}/plots/?${params}`,
    )
  },
})

watch(
  () => route.query.fit_id,
  (fitId) => {
    if (typeof fitId === 'string' && fitId) selectedFitId.value = fitId
  },
  { immediate: true },
)

watch(
  () => displayFits.value,
  (fits) => {
    if (!fits?.length) {
      selectedFitId.value = ''
      selectedRvFitId.value = ''
      return
    }
    const best = fits.find((f) => f.is_best_fit) ?? fits[0]
    if (!selectedFitId.value || !fits.some((f) => f.id === selectedFitId.value)) {
      selectedFitId.value = best.id
    }
    selectedRvFitId.value = selectedFitId.value
  },
  { immediate: true },
)

watch(selectedFitId, async (fitId) => {
  if (!analysis.value || !fitId || displayFits.value.length <= 1) {
    fitParams.value = []
    return
  }
  const best = displayFits.value.find((f) => f.is_best_fit)
  if (best && fitId === best.id) {
    fitParams.value = []
    return
  }
  try {
    const res = await api<{ parameters: FitParameter[] }>(
      `/api/analysis/analyses/${pk.value}/fit-parameters/?fit_id=${encodeURIComponent(fitId)}`,
    )
    fitParams.value = res.parameters
  } catch {
    fitParams.value = []
  }
})

const displayedParameters = computed((): DisplayedParameter[] => {
  if (fitParams.value.length) {
    return fitParams.value.map((param, idx) => ({
      key: `${param.cname}-${idx}`,
      display_label: param.display_label,
      value: param.value,
      error: (param.error_u + param.error_l) / 2,
      valid: null,
    }))
  }
  return (analysis.value?.parameters ?? []).map((param) => ({
    key: String(param.pk),
    display_label: param.display_label,
    value: param.rvalue,
    error: param.rerror,
    valid: param.valid,
    parameterPk: param.pk,
  }))
})

const showFitSelector = computed(() => displayFits.value.length > 1)

const { data: categoryOptions } = useQuery({
  queryKey: ['analysis-categories'],
  queryFn: () => api<{ results: CategoryOption[] }>('/api/analysis/categories/'),
})

const star = computed(() => {
  const value = analysis.value?.star
  return value && 'pk' in value && value.pk ? (value as StarRef) : null
})

const pageTitle = computed(() => {
  if (!analysis.value) return 'Analysis'
  const starName = star.value?.name ?? '—'
  const categoryName = analysis.value.category_label ?? '—'
  return `${starName} — ${categoryName}`
})

const deriveButtonLabel = computed(() => {
  if (deriveBusy.value) return 'Calculating…'
  if (analysis.value?.derived_parameters.length) return 'Recalculate parameters'
  return 'Calculate additional parameters'
})

const analysisDownloadName = computed(() => {
  const path = analysis.value?.datafile
  if (path) {
    const base = path.split('/').pop()
    if (base) return base
  }
  const name = analysis.value?.name?.trim()
  if (name) return name.endsWith('.h5') || name.endsWith('.hdf5') ? name : `${name}.h5`
  return 'analysis.h5'
})

const histPlotKeys = computed(() => {
  if (!plots.value) return []
  return Object.keys(plots.value).filter((key) => key !== 'fit' && key !== 'oc')
})

watch(analysis, (value) => {
  if (!value) return
  noteText.value = value.note || ''
  nameText.value = value.name || ''
  categoryValue.value = value.category || ''
  fitValue.value = value.fit
}, { immediate: true })

function openNoteEdit() {
  noteText.value = analysis.value?.note || ''
  noteEdit.value = true
}

function openDetailsEdit() {
  nameText.value = analysis.value?.name || ''
  categoryValue.value = analysis.value?.category || ''
  fitValue.value = analysis.value?.fit ?? true
  detailsEdit.value = true
}

async function saveNote() {
  await api(`/api/analysis/analyses/${pk.value}/`, {
    method: 'PATCH',
    body: { note: noteText.value.trim() },
  })
  noteEdit.value = false
  await refetch()
}

async function saveDetails() {
  await api(`/api/analysis/analyses/${pk.value}/`, {
    method: 'PATCH',
    body: {
      name: nameText.value.trim(),
      category: categoryValue.value,
      category_source: 'user',
      fit: fitValue.value,
    },
  })
  detailsEdit.value = false
  await refetch()
}

async function toggleParameterValid(parameterPk: number, valid: boolean) {
  try {
    await api(`/api/analysis/parameters/${parameterPk}/`, {
      method: 'PATCH',
      body: { valid },
    })
    await refetch()
  } catch {
    await refetch()
  }
}

async function deriveParameters() {
  if (!analysis.value?.has_derived_definitions || !analysis.value.can_edit) return
  deriveBusy.value = true
  deriveMessage.value = ''
  try {
    const res = await api<{
      created: number
      updated: number
      failed: string[]
    }>(`/api/analysis/analyses/${pk.value}/derive-parameters/`, { method: 'POST' })
    const parts: string[] = []
    if (res.created) parts.push(`${res.created} created`)
    if (res.updated) parts.push(`${res.updated} updated`)
    if (res.failed.length) parts.push(`failed: ${res.failed.join(', ')}`)
    deriveMessage.value = parts.length ? parts.join('; ') : 'Derived parameters up to date'
    await refetch()
  } catch (e) {
    deriveMessage.value = e instanceof Error ? e.message : String(e)
  } finally {
    deriveBusy.value = false
  }
}

async function remove() {
  if (!(await confirmAction({
    title: 'Delete analysis',
    message: 'Are you sure you want to delete this analysis? This cannot be undone.',
  }))) return
  await api(`/api/analysis/analyses/${pk.value}/`, { method: 'DELETE' })
  router.push(`/w/${projectSlug.value}/analysis/analyses/`)
}

async function setBestFit(fitId: string) {
  if (!analysis.value?.can_set_best_fit) return
  fitActionBusy.value = true
  try {
    await api(`/api/analysis/analyses/${pk.value}/best-fit/`, {
      method: 'POST',
      body: { fit_id: fitId },
    })
    await refetch()
  } finally {
    fitActionBusy.value = false
  }
}

async function deleteFit(fitId: string) {
  if (!(await confirmAction({
    title: 'Delete fit',
    message: 'Remove this fit from the container?',
  }))) return
  fitActionBusy.value = true
  try {
    await api(`/api/analysis/analyses/${pk.value}/fits/${encodeURIComponent(fitId)}/`, {
      method: 'DELETE',
    })
    await refetch()
  } finally {
    fitActionBusy.value = false
  }
}

function triggerFitUpload() {
  fitFileInput.value?.click()
}

async function onFitFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  fitActionBusy.value = true
  try {
    const form = new FormData()
    form.append('datafile', file)
    await api(`/api/analysis/analyses/${pk.value}/fits/`, { method: 'POST', body: form })
    await refetch()
  } finally {
    fitActionBusy.value = false
    input.value = ''
  }
}
</script>

<template>
  <div v-if="analysis" class="flex gap-4 items-start">
    <aside
      v-if="analysis.related_analyses.length || analysis.related_by_category.length"
      class="hidden xl:block w-52 shrink-0 aots-panel-compact text-xs sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto space-y-4"
    >
      <div v-if="analysis.related_analyses.length">
        <h2 class="font-medium text-sm mb-2">Related analyses</h2>
        <h3
          v-if="star"
          class="text-aots-muted mb-1"
          :title="'Other analyses for the same star'"
        >
          {{ star.name }}
        </h3>
        <ul class="space-y-0.5">
          <li v-for="item in analysis.related_analyses" :key="item.pk">
            <RouterLink
              :to="`/w/${projectSlug}/analysis/analyses/${item.pk}/`"
              class="block rounded px-1 py-0.5 hover:bg-aots-surface-muted/60"
              :class="item.is_current ? 'bg-aots-highlight text-aots-brand' : ''"
            >
              <template v-if="item.is_current">— {{ item.category_label }} —</template>
              <template v-else>{{ item.category_label }} · {{ item.name }}</template>
            </RouterLink>
          </li>
        </ul>
      </div>

      <div v-if="analysis.related_by_category.length">
        <h3
          class="text-aots-muted mb-1"
          :title="'Other analyses in the same category'"
        >
          {{ analysis.category_label }}
        </h3>
        <ul class="space-y-0.5">
          <li v-for="item in analysis.related_by_category" :key="`category-${item.pk}`">
            <RouterLink
              :to="`/w/${projectSlug}/analysis/analyses/${item.pk}/`"
              class="block rounded px-1 py-0.5 hover:bg-aots-surface-muted/60"
              :class="item.is_current ? 'bg-aots-highlight text-aots-brand' : ''"
            >
              <template v-if="item.is_current">— {{ item.star_name }} —</template>
              <template v-else>{{ item.star_name }} · {{ item.name }}</template>
            </RouterLink>
          </li>
        </ul>
      </div>
    </aside>

    <div class="flex-1 min-w-0 space-y-4">
      <div class="aots-detail-header">
        <div
          v-if="canEdit || canDelete"
          class="absolute top-1 right-1 flex items-center gap-2"
        >
          <AppButton
            v-if="canEdit"
            variant="icon"
            title="Edit analysis"
            @click="openDetailsEdit"
          >
            <Pencil class="w-4 h-4" />
          </AppButton>
          <AppButton
            v-if="canDelete"
            variant="ghost-danger"
            size="sm"
            class="inline-flex items-center gap-1.5"
            @click="remove"
          >
            <Trash2 class="w-3.5 h-3.5" /> Delete analysis
          </AppButton>
        </div>

        <h1 class="text-lg font-semibold m-0 w-full xl:w-auto">
          {{ pageTitle }}<span v-if="analysis.name" class="font-medium text-aots-muted"> ({{ analysis.name }})</span>
        </h1>

        <div v-if="star" class="flex items-center gap-1.5">
          <Star class="w-4 h-4 text-amber-400 shrink-0" />
          <AppButton
            variant="link"
            class="font-medium"
            :to="`/w/${projectSlug}/systems/stars/${star.pk}`"
          >
            {{ star.name }}
          </AppButton>
        </div>

        <div class="flex items-center gap-1.5 text-sm">
          <span
            class="inline-flex items-center gap-1.5"
            :class="analysis.category === 'unknown' ? 'text-amber-300' : ''"
          >
            <span
              class="inline-block w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ backgroundColor: analysis.category_color }"
            />
            {{ analysis.category_label }}
          </span>
        </div>

        <div v-if="analysis.reference" class="flex items-center gap-1.5 text-sm">
          <BookOpen class="w-4 h-4 text-aots-muted shrink-0" />
          <AppButton
            variant="link"
            :href="analysis.reference_url"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ analysis.reference }}
          </AppButton>
        </div>

        <div class="flex items-center gap-2 text-sm text-aots-muted">
          <input
            type="checkbox"
            class="accent-aots pointer-events-none"
            :checked="analysis.fit"
            tabindex="-1"
            aria-hidden="true"
          />
          <span>Fit</span>
        </div>

        <div v-if="analysis.file_url && auth.isAuthenticated" class="flex items-center gap-1.5">
          <AppButton
            variant="secondary"
            size="sm"
            class="inline-flex items-center gap-1"
            :href="analysis.file_url"
            :download="analysisDownloadName"
            title="Download HDF5 analysis file"
          >
            <Download class="w-3.5 h-3.5" />
            Download HDF5
          </AppButton>
        </div>
      </div>

      <div class="grid gap-4 xl:grid-cols-2">
        <section class="aots-panel-compact space-y-4 min-w-0 overflow-hidden">
          <div
            v-if="showFitSelector"
            class="flex flex-wrap items-center gap-2 text-sm"
          >
            <label for="fit-select" class="text-aots-muted">Model fit</label>
            <select
              id="fit-select"
              v-model="selectedFitId"
              class="aots-input text-sm"
            >
              <option v-for="fit in displayFits" :key="fit.id" :value="fit.id">
                {{ fit.label }}{{ fit.is_best_fit ? ' (best)' : '' }}
                <template v-if="fit.uploaded_by?.username"> — {{ fit.uploaded_by.username }}</template>
              </option>
            </select>
            <AppButton
              v-if="analysis.can_set_best_fit && selectedFitId && !displayFits.find(f => f.id === selectedFitId)?.is_best_fit"
              variant="secondary"
              size="sm"
              :disabled="fitActionBusy"
              @click="setBestFit(selectedFitId)"
            >
              Mark as best fit
            </AppButton>
          </div>

          <div v-if="displayFits.length" class="text-xs space-y-1">
            <div
              v-for="fit in displayFits"
              :key="fit.id"
              class="flex flex-wrap items-center gap-2"
            >
              <span class="text-aots-muted">
                {{ fit.label }}
                <span v-if="fit.uploaded_by?.username">({{ fit.uploaded_by.username }})</span>
                <span v-if="fit.is_best_fit" class="text-aots-brand">best</span>
              </span>
              <AppButton
                v-if="fit.can_delete"
                variant="link"
                size="sm"
                class="text-red-600"
                :disabled="fitActionBusy"
                @click="deleteFit(fit.id)"
              >
                <Trash2 class="w-3 h-3" />
              </AppButton>
            </div>
            <div v-if="canEdit" class="pt-1">
              <input ref="fitFileInput" type="file" accept=".h5,.hdf5" class="hidden" @change="onFitFileSelected" />
              <AppButton variant="secondary" size="sm" :disabled="fitActionBusy" @click="triggerFitUpload">
                Contribute fit
              </AppButton>
            </div>
          </div>
          <div v-if="plots?.fit" class="w-full max-w-full min-w-0">
            <BokehPlot compact :item="plots.fit.item" />
          </div>
          <div v-if="plots?.oc" class="w-full max-w-full min-w-0">
            <BokehPlot compact :item="plots.oc.item" />
          </div>
        </section>

        <div class="space-y-4 min-w-0">
          <section class="aots-panel-compact">
            <h2 class="text-sm font-medium mb-2">Parameters</h2>
            <div class="overflow-x-auto">
              <table class="aots-param-table">
                <thead>
                  <tr>
                    <th>Parameter</th>
                    <th>Value</th>
                    <th>Error</th>
                    <th>Valid</th>
                  </tr>
                </thead>
                <tbody class="font-mono">
                  <tr v-if="!displayedParameters.length">
                    <td colspan="4" class="text-aots-muted">No data available</td>
                  </tr>
                  <tr v-for="param in displayedParameters" :key="param.key">
                    <th class="font-normal text-aots">
                      {{ param.display_label }}
                    </th>
                    <td>{{ param.value }}</td>
                    <td>{{ param.error }}</td>
                    <td>
                      <input
                        v-if="param.parameterPk != null && param.valid != null"
                        type="checkbox"
                        class="accent-aots"
                        :checked="param.valid"
                        :disabled="!canEdit"
                        @change="toggleParameterValid(param.parameterPk, ($event.target as HTMLInputElement).checked)"
                      />
                      <span v-else class="text-aots-muted">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section v-if="analysis.has_derived_definitions" class="aots-panel-compact">
            <div class="flex items-center justify-between gap-2 mb-2">
              <h2 class="text-sm font-medium m-0">Derived parameters</h2>
              <AppButton
                v-if="canEdit && star"
                variant="secondary"
                size="sm"
                :disabled="deriveBusy"
                @click="deriveParameters"
              >
                {{ deriveButtonLabel }}
              </AppButton>
            </div>
            <p v-if="deriveMessage" class="text-xs text-aots-muted mb-2">{{ deriveMessage }}</p>
            <p class="text-xs text-aots-faint-extra mb-2">
              Star-level averages for this category (not stored on the analysis file itself).
            </p>
            <div class="overflow-x-auto">
              <table class="aots-param-table">
                <thead>
                  <tr>
                    <th>Parameter</th>
                    <th>Value</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody class="font-mono">
                  <tr v-if="!analysis.derived_parameters.length">
                    <td colspan="3" class="text-aots-muted">
                      Not calculated yet
                      <template v-if="canEdit"> — use the button above</template>
                    </td>
                  </tr>
                  <tr v-for="param in analysis.derived_parameters" :key="param.pk">
                    <th class="font-normal text-aots">
                      {{ param.display_label }}
                    </th>
                    <td>{{ param.rvalue }}</td>
                    <td>{{ param.rerror }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="aots-panel-compact relative">
            <h2 class="text-sm font-medium mb-2">Notes</h2>
            <AppButton
              v-if="canEdit"
              variant="icon"
              class="absolute top-2 right-2"
              title="Edit note"
              @click="openNoteEdit"
            >
              <Pencil class="w-4 h-4" />
            </AppButton>
            <div class="text-sm text-aots whitespace-pre-wrap pr-8">
              {{ analysis.note || '—' }}
            </div>
          </section>

          <section class="aots-panel-compact">
            <h2 class="text-sm font-medium mb-2">Meta data</h2>
            <table class="aots-kv-table">
              <tbody>
                <tr>
                  <th>Added by</th>
                  <td>{{ analysis.added_by }}</td>
                </tr>
                <tr>
                  <th>Added on</th>
                  <td>{{ analysis.added_on }}</td>
                </tr>
                <tr>
                  <th>Last modified</th>
                  <td>{{ analysis.last_modified }}</td>
                </tr>
                <tr>
                  <th>Modified by</th>
                  <td>{{ analysis.modified_by }}</td>
                </tr>
                <tr v-if="analysis.file_type">
                  <th>File type</th>
                  <td>{{ analysis.file_type }}</td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </div>

      <section v-if="histPlotKeys.length" class="space-y-4">
        <h2 class="text-sm font-medium">Parameter distribution</h2>
        <div class="grid gap-4 lg:grid-cols-2">
          <div
            v-for="key in histPlotKeys"
            :key="key"
            class="aots-panel-compact min-w-0 overflow-hidden"
          >
            <div class="w-full max-w-full min-w-0">
              <BokehPlot
                v-if="plots?.[key]"
                compact
                :item="plots[key].item"
              />
            </div>
          </div>
        </div>
      </section>
    </div>

    <dialog
      v-if="noteEdit"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="noteEdit = false"
    >
      <div class="aots-panel w-full max-w-lg">
        <h3 class="font-medium mb-3">Edit notes</h3>
        <textarea v-model="noteText" rows="5" class="aots-field w-full font-mono text-sm" />
        <div class="flex gap-2 mt-4">
          <AppButton variant="primary" @click="saveNote">Update</AppButton>
          <AppButton variant="ghost" @click="noteEdit = false">Cancel</AppButton>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="detailsEdit"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="detailsEdit = false"
    >
      <div class="aots-panel w-full max-w-lg space-y-4">
        <h3 class="font-medium">Edit analysis</h3>
        <label class="block space-y-1">
          <span class="text-sm text-aots-muted">Name</span>
          <textarea v-model="nameText" rows="2" class="aots-field w-full font-mono text-sm" />
        </label>
        <label class="block space-y-1">
          <span class="text-sm text-aots-muted">Category</span>
          <select v-model="categoryValue" class="aots-select w-full">
            <option
              v-for="option in categoryOptions?.results ?? []"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="flex items-center gap-2 text-sm cursor-pointer">
          <input v-model="fitValue" type="checkbox" class="accent-aots" />
          <span>Fit (analysis contains fit results)</span>
        </label>
        <div class="flex gap-2">
          <AppButton variant="primary" @click="saveDetails">Update</AppButton>
          <AppButton variant="ghost" @click="detailsEdit = false">Cancel</AppButton>
        </div>
      </div>
    </dialog>
  </div>
</template>
