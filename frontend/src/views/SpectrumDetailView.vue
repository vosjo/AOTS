<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { CheckCircle2, Download, Pencil, Star, Trash2, XCircle, FileText } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

interface StarRef {
  pk: number
  name: string
}

interface SpecFileRef {
  pk: number
  filetype: string
  download_url: string
  header_url: string
}

interface RelatedSpectrum {
  pk: number
  hjd: number
  hjd_date: string
  is_current: boolean
}

interface RelatedGroup {
  instrument: string
  spectra: RelatedSpectrum[]
}

interface SpectrumDetail {
  pk: number
  title: string
  star: StarRef | ''
  valid: boolean
  fluxcal: boolean
  flux_units: string
  note: string
  objectname: string
  target_coords: string
  obs_coords: string
  hjd: number
  hjd_date: string
  hjd_datetime: string
  instrument: string
  telescope: string
  observer: string
  resolution_display: string
  exptime_display: string
  snr_display: string
  seeing_display: string
  airmass_display: string
  moon_illumination_display: string
  moon_separation_display: string
  wind_display: string
  weather_url: string
  observatory_short_name: string
  normalized: boolean
  decomposed: boolean
  master: boolean
  barycor: number
  specfiles: SpecFileRef[]
  default_rebin: number
  related_spectra: RelatedGroup[]
}

import type { BokehEmbed } from '@/types/bokeh'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const themeStore = useThemeStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const pk = computed(() => route.params.id as string)

const noteEdit = ref(false)
const noteText = ref('')
const spectrumEdit = ref(false)
const editValid = ref(true)
const editFluxcal = ref(false)
const editFluxUnits = ref('')

const headerDialog = ref(false)
const headerTitle = ref('')
const headerEntries = ref<Array<[string, string]>>([])
const headerLoading = ref(false)

const formNormalize = ref(true)
const formPorder = ref(3)
const formRebin = ref(1)
const appliedPlot = ref({ normalize: true, porder: 3, rebin: 1 })

const { data: spectrum, refetch } = useQuery({
  queryKey: computed(() => ['spectrum', pk.value]),
  queryFn: () => api<SpectrumDetail>(`/api/observations/spectra/${pk.value}/`),
})

const { data: visibilityPlot, isFetching: visibilityLoading } = useQuery({
  queryKey: computed(() => ['spectrum-visibility', pk.value, themeStore.mode]),
  queryFn: () =>
    api<{ visibility: BokehEmbed }>(
      `/api/observations/spectra/${pk.value}/plot/?part=visibility&theme=${themeStore.mode}`,
    ),
})

const { data: specPlot, isFetching: specLoading } = useQuery({
  queryKey: computed(() => ['spectrum-spec-plot', pk.value, appliedPlot.value, themeStore.mode]),
  queryFn: () => {
    const q = new URLSearchParams({
      part: 'spec',
      rebin: String(appliedPlot.value.rebin),
      normalize: appliedPlot.value.normalize ? 'true' : 'false',
      porder: String(appliedPlot.value.porder),
      theme: themeStore.mode,
    })
    return api<{ spec: BokehEmbed }>(
      `/api/observations/spectra/${pk.value}/plot/?${q}`,
    )
  },
})

const star = computed(() => {
  const s = spectrum.value?.star
  return s && typeof s === 'object' ? s : null
})

const normalizeDisabled = computed(() => spectrum.value?.normalized === true)
const orderDisabled = computed(
  () => normalizeDisabled.value || !formNormalize.value,
)

watch(spectrum, (s) => {
  if (!s) return
  noteText.value = s.note || ''
  formRebin.value = s.default_rebin
  appliedPlot.value = {
    normalize: true,
    porder: 3,
    rebin: s.default_rebin,
  }
}, { immediate: true })

function updateFigure() {
  appliedPlot.value = {
    normalize: formNormalize.value,
    porder: formPorder.value,
    rebin: formRebin.value,
  }
}

function openSpectrumEdit() {
  if (!spectrum.value) return
  editValid.value = spectrum.value.valid
  editFluxcal.value = spectrum.value.fluxcal
  editFluxUnits.value = spectrum.value.flux_units
  spectrumEdit.value = true
}

async function saveNote() {
  await api(`/api/observations/spectra/${pk.value}/`, {
    method: 'PATCH',
    body: { note: noteText.value },
  })
  noteEdit.value = false
  refetch()
}

async function saveSpectrumEdit() {
  await api(`/api/observations/spectra/${pk.value}/`, {
    method: 'PATCH',
    body: {
      valid: editValid.value,
      fluxcal: editFluxcal.value,
      flux_units: editFluxUnits.value,
    },
  })
  spectrumEdit.value = false
  refetch()
}

async function showHeader(file: SpecFileRef) {
  headerTitle.value = file.filetype
  headerDialog.value = true
  headerLoading.value = true
  headerEntries.value = []
  try {
    const data = await api<Record<string, string>>(file.header_url)
    headerEntries.value = Object.entries(data)
  } finally {
    headerLoading.value = false
  }
}

function yesNo(value: boolean) {
  return value ? 'Yes' : 'No'
}

async function remove() {
  if (!confirm('Are you sure you want to delete this spectrum? This can NOT be undone.')) return
  await api(`/api/observations/spectra/${pk.value}/`, { method: 'DELETE' })
  router.push(`/w/${projectSlug.value}/observations/spectra/`)
}
</script>

<template>
  <div v-if="spectrum" class="flex gap-4 items-start">
    <aside
      v-if="star && spectrum.related_spectra.length"
      class="hidden xl:block w-52 shrink-0 aots-panel-compact text-xs sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto"
    >
      <h2 class="font-medium text-sm mb-2">
        All spectra for <span class="whitespace-nowrap">{{ star.name }}</span>
      </h2>
      <div v-for="group in spectrum.related_spectra" :key="group.instrument" class="mb-3">
        <h3 class="text-aots-muted font-medium mb-1">{{ group.instrument }}</h3>
        <ul class="space-y-0.5">
          <li v-for="spec in group.spectra" :key="spec.pk">
            <RouterLink
              :to="`/w/${projectSlug}/observations/spectra/${spec.pk}/`"
              class="block rounded px-1 py-0.5 hover:bg-aots-surface-muted/60"
              :class="spec.is_current ? 'bg-aots-highlight text-aots-brand' : ''"
            >
              {{ spec.hjd.toFixed(3) }} — {{ spec.hjd_date }}
            </RouterLink>
          </li>
        </ul>
      </div>
    </aside>

    <div class="flex-1 min-w-0 space-y-3">
      <div class="aots-detail-header">
        <AppButton
          v-if="auth.isAuthenticated"
          variant="icon"
          class="absolute top-1 right-1"
          title="Edit spectrum"
          @click="openSpectrumEdit"
        >
          <Pencil class="w-4 h-4" />
        </AppButton>

        <div class="flex items-center gap-2">
          <h1 class="text-lg font-semibold m-0">{{ spectrum.title }}</h1>
        </div>

        <div v-if="star" class="flex items-center gap-1.5">
          <Star class="w-4 h-4 text-amber-400 shrink-0" />
          <RouterLink
            :to="`/w/${projectSlug}/systems/stars/${star.pk}`"
            class="font-medium"
          >
            {{ star.name }}
          </RouterLink>
        </div>

        <div class="flex items-center gap-1.5 text-sm">
          <CheckCircle2
            v-if="spectrum.valid"
            class="w-4 h-4 text-emerald-400"
            title="Good quality"
          />
          <XCircle
            v-else
            class="w-4 h-4 text-red-400"
            title="Bad quality"
          />
          <span>Valid</span>
        </div>

        <div class="flex items-center gap-1.5 text-sm">
          <CheckCircle2
            v-if="spectrum.fluxcal"
            class="w-4 h-4 text-emerald-400"
            title="Flux calibrated"
          />
          <XCircle
            v-else
            class="w-4 h-4 text-red-400"
            title="Not flux calibrated"
          />
          <span>Flux calibrated</span>
        </div>
      </div>

      <div class="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_minmax(220px,0.9fr)_minmax(180px,0.7fr)] lg:items-stretch">
        <section class="aots-panel-compact flex min-h-0 flex-col">
          <h2 class="text-sm font-medium mb-2 shrink-0">Basic data</h2>
          <div class="grid sm:grid-cols-2 gap-x-4">
            <table class="aots-kv-table">
              <tbody>
                <tr><th>Target:</th><td>{{ spectrum.objectname || '—' }}</td></tr>
                <tr><th>Target coord.:</th><td>{{ spectrum.target_coords || '—' }}</td></tr>
                <tr><th>Obs. coord.:</th><td>{{ spectrum.obs_coords || '—' }}</td></tr>
                <tr><th>HJD:</th><td>{{ spectrum.hjd }}</td></tr>
                <tr><th>Date:</th><td>{{ spectrum.hjd_datetime }}</td></tr>
                <tr><th>Instrument:</th><td>{{ spectrum.instrument }} @ {{ spectrum.telescope }}</td></tr>
                <tr><th>Observer:</th><td>{{ spectrum.observer || '—' }}</td></tr>
                <tr><th>Resolution:</th><td>{{ spectrum.resolution_display }}</td></tr>
                <tr><th>Exposure:</th><td>{{ spectrum.exptime_display }}</td></tr>
                <tr><th>SNR:</th><td>{{ spectrum.snr_display }}</td></tr>
              </tbody>
            </table>
            <table class="aots-kv-table">
              <tbody>
                <tr><th>Seeing:</th><td>{{ spectrum.seeing_display }}</td></tr>
                <tr><th>Airmass:</th><td>{{ spectrum.airmass_display }}</td></tr>
                <tr><th>Moon illumination:</th><td>{{ spectrum.moon_illumination_display }}</td></tr>
                <tr><th>Moon separation:</th><td>{{ spectrum.moon_separation_display }}</td></tr>
                <tr><th>Wind:</th><td>{{ spectrum.wind_display }}</td></tr>
                <tr>
                  <th>Weather link:</th>
                  <td>
                    <a
                      v-if="spectrum.weather_url"
                      :href="spectrum.weather_url"
                      target="_blank"
                      rel="noopener"
                    >
                      {{ spectrum.observatory_short_name }}
                    </a>
                    <span v-else>NA</span>
                  </td>
                </tr>
                <tr><th>Normalized:</th><td>{{ yesNo(spectrum.normalized) }}</td></tr>
                <tr><th>Flux calibrated:</th><td>{{ yesNo(spectrum.fluxcal) }}</td></tr>
                <tr><th>Decomposed:</th><td>{{ yesNo(spectrum.decomposed) }}</td></tr>
                <tr><th>Master:</th><td>{{ yesNo(spectrum.master) }}</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="aots-panel-compact flex min-h-0 flex-col lg:h-full">
          <h2 class="text-sm font-medium mb-2 shrink-0">Visibility</h2>
          <div class="min-h-[260px] sm:min-h-[300px] lg:min-h-0 flex-1 w-full overflow-hidden">
            <div
              v-if="visibilityLoading && !visibilityPlot?.visibility"
              class="h-full min-h-[260px] sm:min-h-[300px] rounded bg-aots-surface-muted/40 animate-pulse"
            />
            <BokehPlot
              v-else-if="visibilityPlot?.visibility"
              fill
              :item="visibilityPlot.visibility.item"
            />
          </div>
        </section>

        <section class="aots-panel-compact flex h-full min-h-0 min-w-0 flex-col">
          <div class="flex min-h-0 flex-1 flex-col gap-3">
            <div class="min-w-0">
              <h2 class="text-sm font-medium mb-1">Files</h2>
              <ul v-if="spectrum.specfiles.length" class="text-xs space-y-1 min-w-0">
                <li
                  v-for="file in spectrum.specfiles"
                  :key="file.pk"
                  class="flex min-w-0 flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-center"
                >
                  <span
                    class="min-w-0 break-all font-mono text-aots leading-snug"
                    :title="file.filetype"
                  >
                    {{ file.filetype }}
                  </span>
                  <span class="flex shrink-0 items-center gap-3">
                    <AppButton variant="link" @click="showHeader(file)">
                      <FileText class="w-3.5 h-3.5" /> (Header)
                    </AppButton>
                    <AppButton
                      v-if="auth.isAuthenticated && file.download_url"
                      variant="link"
                      :href="file.download_url"
                      title="Download"
                    >
                      <Download class="w-3.5 h-3.5" /> (FITS)
                    </AppButton>
                  </span>
                </li>
              </ul>
              <p v-else class="text-xs text-aots-muted">No files</p>
            </div>

            <div class="border-t border-aots pt-2 relative">
              <h2 class="text-sm font-medium">Note</h2>
              <AppButton
                v-if="auth.isAuthenticated"
                variant="icon"
                class="absolute top-2 right-0"
                title="Edit note"
                @click="noteEdit = !noteEdit"
              >
                <Pencil class="w-4 h-4" />
              </AppButton>
              <p v-if="!noteEdit" class="text-xs text-aots-muted mt-1 whitespace-pre-wrap pr-8">
                {{ spectrum.note || '—' }}
              </p>
              <div v-else class="mt-2 space-y-2">
                <textarea v-model="noteText" class="aots-field text-xs" rows="4" />
                <AppButton variant="primary" size="sm" @click="saveNote">Save</AppButton>
              </div>
            </div>
          </div>

          <div
            v-if="auth.isAuthenticated"
            class="mt-auto shrink-0 border-t border-aots pt-2"
          >
            <AppButton
              variant="ghost-danger"
              size="sm"
              @click="remove"
            >
              <Trash2 class="w-3.5 h-3.5" /> Delete spectrum
            </AppButton>
          </div>
        </section>
      </div>

      <section class="aots-panel-compact">
        <h2 class="text-sm font-medium mb-1">The spectrum</h2>
        <p class="text-xs text-aots-muted mb-3">
          The spectrum is shifted with a barycentric correction of
          {{ spectrum.barycor.toFixed(2) }} km/s.
        </p>

        <div class="flex flex-col gap-2">
          <div class="w-full max-w-full min-w-0 overflow-hidden min-h-0">
            <div
              v-if="specLoading && !specPlot?.spec"
              class="h-[220px] sm:h-[360px] rounded bg-aots-surface-muted/40 animate-pulse"
            />
            <BokehPlot
              v-else-if="specPlot?.spec"
              compact
              :item="specPlot.spec.item"
            />
          </div>

          <div class="w-full border border-aots rounded-md p-3 bg-aots-page/40">
            <h3 class="text-sm font-medium mb-2">Modify data</h3>
            <form class="text-xs" @submit.prevent="updateFigure">
              <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                <label
                  class="flex items-center gap-1.5 shrink-0"
                  :class="normalizeDisabled ? 'opacity-50' : ''"
                >
                  <input
                    v-model="formNormalize"
                    type="checkbox"
                    :disabled="normalizeDisabled"
                  />
                  Normalize
                </label>
                <div
                  class="flex items-center gap-1.5"
                  :class="orderDisabled ? 'opacity-50' : ''"
                >
                  <span class="text-aots-muted whitespace-nowrap">Order</span>
                  <input
                    v-model.number="formPorder"
                    type="number"
                    min="1"
                    max="15"
                    class="aots-field-sm w-14"
                    :disabled="orderDisabled"
                  />
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="text-aots-muted whitespace-nowrap">Binning</span>
                  <input
                    v-model.number="formRebin"
                    type="number"
                    min="1"
                    max="100"
                    class="aots-field-sm w-16"
                  />
                </div>
                <AppButton
                  type="submit"
                  variant="primary"
                  size="sm"
                  class="w-full sm:w-auto sm:ml-auto"
                >
                  Update figure
                </AppButton>
              </div>
            </form>
          </div>
        </div>
      </section>
    </div>

    <dialog
      v-if="headerDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="headerDialog = false"
    >
      <div class="aots-panel max-h-[90vh] w-full max-w-2xl overflow-hidden flex flex-col">
        <div class="flex justify-between items-center mb-3">
          <h2 class="font-medium">{{ headerTitle }} header</h2>
          <AppButton variant="ghost" @click="headerDialog = false">
            Close
          </AppButton>
        </div>
        <div class="overflow-y-auto text-xs font-mono">
          <p v-if="headerLoading" class="text-aots-muted">Loading…</p>
          <ul v-else class="space-y-1">
            <li v-for="[key, value] in headerEntries" :key="key">
              <span class="text-aots-muted">{{ key }}</span>:
              <span class="text-aots">{{ value }}</span>
            </li>
          </ul>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="spectrumEdit"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="spectrumEdit = false"
    >
      <div class="aots-panel w-full max-w-md">
        <h2 class="font-medium mb-3">Edit spectrum</h2>
        <ul class="space-y-3 text-sm">
          <li>
            <label class="flex items-center gap-2">
              <input v-model="editValid" type="checkbox" />
              Valid
            </label>
          </li>
          <li>
            <label class="flex items-center gap-2">
              <input v-model="editFluxcal" type="checkbox" />
              Flux calibrated
            </label>
          </li>
          <li>
            <label class="block">
              <span class="aots-label">Flux units</span>
              <input v-model="editFluxUnits" type="text" class="aots-field" />
            </label>
          </li>
        </ul>
        <div class="flex justify-end gap-2 mt-4">
          <AppButton variant="ghost" @click="spectrumEdit = false">Cancel</AppButton>
          <AppButton variant="primary" @click="saveSpectrumEdit">Update</AppButton>
        </div>
      </div>
    </dialog>
  </div>
</template>
