<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { CheckCircle2, Download, Pencil, Star, XCircle } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

interface StarRef {
  pk: number
  name: string
}

interface RelatedLightcurve {
  pk: number
  hjd: number
  hjd_date: string
  is_current: boolean
}

interface RelatedGroup {
  instrument: string
  lightcurves: RelatedLightcurve[]
}

interface LightcurveDetail {
  pk: number
  title: string
  star: StarRef | ''
  valid: boolean
  note: string
  objectname: string
  target_coords: string
  obs_coords: string
  hjd: number
  hjd_datetime: string
  instrument: string
  telescope: string
  passband: string
  observer: string
  exptime_display: string
  cadence_display: string
  duration_display: string
  seeing_display: string
  moon_illumination_display: string
  wind_display: string
  weather_url: string
  observatory_short_name: string
  filetype: string
  download_url: string
  header_url: string
  exptime: number
  related_lightcurves: RelatedGroup[]
}

interface BokehEmbed {
  script: string
  div: string
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const pk = computed(() => route.params.id as string)

const noteEdit = ref(false)
const noteText = ref('')
const lcEdit = ref(false)
const editValid = ref(true)
const editExptime = ref('')

const headerDialog = ref(false)
const headerEntries = ref<Array<[string, string]>>([])
const headerLoading = ref(false)

const formPeriod = ref('')
const formBinsize = ref('0.001')
const appliedPhase = ref({ period: '', binsize: '0.001' })

const { data: lc, refetch } = useQuery({
  queryKey: computed(() => ['lightcurve', pk.value]),
  queryFn: () => api<LightcurveDetail>(`/api/observations/lightcurves/${pk.value}/`),
})

const { data: visibilityPlot, isFetching: visibilityLoading } = useQuery({
  queryKey: computed(() => ['lightcurve-visibility', pk.value]),
  queryFn: () =>
    api<{ visibility: BokehEmbed }>(
      `/api/observations/lightcurves/${pk.value}/plot/?part=visibility`,
    ),
})

const { data: timePlot, isFetching: timeLoading } = useQuery({
  queryKey: computed(() => ['lightcurve-time', pk.value]),
  queryFn: () =>
    api<{ lc_time: BokehEmbed }>(
      `/api/observations/lightcurves/${pk.value}/plot/?part=lc_time`,
    ),
})

const { data: phasePlot, isFetching: phaseLoading } = useQuery({
  queryKey: computed(() => ['lightcurve-phase', pk.value, appliedPhase.value]),
  queryFn: () => {
    const q = new URLSearchParams({ part: 'lc_phase' })
    if (appliedPhase.value.period) q.set('period', appliedPhase.value.period)
    q.set('binsize', appliedPhase.value.binsize)
    return api<{ lc_phase: BokehEmbed }>(
      `/api/observations/lightcurves/${pk.value}/plot/?${q}`,
    )
  },
})

const star = computed(() => {
  const s = lc.value?.star
  return s && typeof s === 'object' ? s : null
})

watch(lc, (data) => {
  if (!data) return
  noteText.value = data.note || ''
  editExptime.value = data.exptime >= 0 ? String(data.exptime) : ''
}, { immediate: true })

function updatePhasePlot() {
  appliedPhase.value = {
    period: formPeriod.value,
    binsize: formBinsize.value || '0.001',
  }
}

function openLcEdit() {
  if (!lc.value) return
  editValid.value = lc.value.valid
  editExptime.value = lc.value.exptime >= 0 ? String(lc.value.exptime) : ''
  lcEdit.value = true
}

async function saveNote() {
  await api(`/api/observations/lightcurves/${pk.value}/`, {
    method: 'PATCH',
    body: { note: noteText.value },
  })
  noteEdit.value = false
  refetch()
}

async function saveLcEdit() {
  const exptime = parseFloat(editExptime.value)
  await api(`/api/observations/lightcurves/${pk.value}/`, {
    method: 'PATCH',
    body: {
      valid: editValid.value,
      exptime: Number.isFinite(exptime) ? exptime : -1,
    },
  })
  lcEdit.value = false
  refetch()
}

async function showHeader() {
  if (!lc.value?.header_url) return
  headerDialog.value = true
  headerLoading.value = true
  headerEntries.value = []
  try {
    const data = await api<Record<string, string>>(lc.value.header_url)
    headerEntries.value = Object.entries(data)
  } finally {
    headerLoading.value = false
  }
}

async function remove() {
  if (!confirm('Are you sure you want to delete this light curve? This can NOT be undone.')) return
  await api(`/api/observations/lightcurves/${pk.value}/`, { method: 'DELETE' })
  router.push(`/w/${projectSlug.value}/observations/lightcurves/`)
}
</script>

<template>
  <div v-if="lc" class="flex gap-4 items-start">
    <aside
      v-if="star && lc.related_lightcurves.length"
      class="hidden xl:block w-52 shrink-0 aots-panel-compact text-xs sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto"
    >
      <h2 class="font-medium text-sm mb-2">
        All light curves for <span class="whitespace-nowrap">{{ star.name }}</span>
      </h2>
      <div v-for="group in lc.related_lightcurves" :key="group.instrument" class="mb-3">
        <h3 class="text-slate-400 font-medium mb-1">{{ group.instrument }}</h3>
        <ul class="space-y-0.5">
          <li v-for="item in group.lightcurves" :key="item.pk">
            <RouterLink
              :to="`/w/${projectSlug}/observations/lightcurves/${item.pk}/`"
              class="block rounded px-1 py-0.5 hover:bg-slate-700/60"
              :class="item.is_current ? 'bg-sky-900/40 text-sky-300' : ''"
            >
              {{ item.hjd.toFixed(3) }} — {{ item.hjd_date }}
            </RouterLink>
          </li>
        </ul>
      </div>
    </aside>

    <div class="flex-1 min-w-0 space-y-3">
      <div class="aots-detail-header">
        <button
          v-if="auth.isAuthenticated"
          type="button"
          class="absolute top-1 right-1 p-1 text-slate-300 hover:text-sky-400"
          title="Edit light curve"
          @click="openLcEdit"
        >
          <Pencil class="w-4 h-4" />
        </button>

        <h1 class="text-lg font-semibold m-0">{{ lc.title }}</h1>

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
            v-if="lc.valid"
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
      </div>

      <div class="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_minmax(220px,0.9fr)_minmax(180px,0.7fr)]">
        <section class="aots-panel-compact">
          <h2 class="text-sm font-medium mb-2">Basic data</h2>
          <div class="grid sm:grid-cols-2 gap-x-4">
            <table class="aots-kv-table">
              <tbody>
                <tr><th>Target:</th><td>{{ lc.objectname || '—' }}</td></tr>
                <tr><th>Target coord.:</th><td>{{ lc.target_coords || '—' }}</td></tr>
                <tr><th>Obs. coord.:</th><td>{{ lc.obs_coords || '—' }}</td></tr>
                <tr><th>HJD:</th><td>{{ lc.hjd }}</td></tr>
                <tr><th>Date:</th><td>{{ lc.hjd_datetime }}</td></tr>
                <tr><th>Instrument:</th><td>{{ lc.instrument }} @ {{ lc.telescope }}</td></tr>
                <tr><th>Passband:</th><td>{{ lc.passband || '—' }}</td></tr>
                <tr><th>Observer:</th><td>{{ lc.observer || '—' }}</td></tr>
              </tbody>
            </table>
            <table class="aots-kv-table">
              <tbody>
                <tr><th>Exposure:</th><td>{{ lc.exptime_display }}</td></tr>
                <tr><th>Cadence:</th><td>{{ lc.cadence_display }}</td></tr>
                <tr><th>Duration:</th><td>{{ lc.duration_display }}</td></tr>
                <tr><th>Seeing:</th><td>{{ lc.seeing_display }}</td></tr>
                <tr><th>Moon illumination:</th><td>{{ lc.moon_illumination_display }}</td></tr>
                <tr><th>Wind:</th><td>{{ lc.wind_display }}</td></tr>
                <tr>
                  <th>Weather link:</th>
                  <td>
                    <a
                      v-if="lc.weather_url"
                      :href="lc.weather_url"
                      target="_blank"
                      rel="noopener"
                    >
                      {{ lc.observatory_short_name }}
                    </a>
                    <span v-else>NA</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="aots-panel-compact">
          <h2 class="text-sm font-medium mb-2">Visibility</h2>
          <div class="min-h-[180px] w-full max-w-full min-w-0 overflow-hidden">
            <div
              v-if="visibilityLoading && !visibilityPlot?.visibility"
              class="h-[180px] rounded bg-slate-700/40 animate-pulse"
            />
            <BokehPlot
              v-else-if="visibilityPlot?.visibility"
              :script="visibilityPlot.visibility.script"
              :div="visibilityPlot.visibility.div"
            />
          </div>
        </section>

        <section class="aots-panel-compact space-y-3">
          <div>
            <h2 class="text-sm font-medium mb-1">Light curve files</h2>
            <ul v-if="lc.filetype" class="text-xs space-y-1">
              <li class="flex flex-wrap items-center gap-1">
                <span>{{ lc.filetype }}</span>
                <button
                  type="button"
                  class="text-sky-400 hover:text-sky-300"
                  @click="showHeader"
                >
                  (header)
                </button>
                <a
                  v-if="auth.isAuthenticated && lc.download_url"
                  :href="lc.download_url"
                  class="inline-flex text-sky-400 hover:text-sky-300"
                  title="Download"
                >
                  <Download class="w-3.5 h-3.5" />
                </a>
              </li>
            </ul>
            <p v-else class="text-xs text-slate-400">No files</p>
          </div>

          <div class="border-t border-slate-600 pt-2 relative">
            <h2 class="text-sm font-medium">Note</h2>
            <button
              v-if="auth.isAuthenticated"
              type="button"
              class="absolute top-2 right-0 p-1 text-slate-300 hover:text-sky-400"
              title="Edit note"
              @click="noteEdit = !noteEdit"
            >
              <Pencil class="w-4 h-4" />
            </button>
            <p v-if="!noteEdit" class="text-xs text-slate-300 mt-1 whitespace-pre-wrap pr-8">
              {{ lc.note || '—' }}
            </p>
            <div v-else class="mt-2 space-y-2">
              <textarea v-model="noteText" class="aots-field text-xs" rows="4" />
              <button type="button" class="aots-btn-primary text-xs" @click="saveNote">Save</button>
            </div>
          </div>

          <button
            v-if="auth.isAuthenticated"
            type="button"
            class="text-xs text-red-400 hover:text-red-300"
            @click="remove"
          >
            Delete light curve
          </button>
        </section>
      </div>

      <section class="aots-panel-compact">
        <h2 class="text-sm font-medium mb-2">Light curve (time)</h2>
        <div class="w-full max-w-full min-w-0 overflow-hidden">
          <div
            v-if="timeLoading && !timePlot?.lc_time"
            class="h-[220px] sm:h-[320px] rounded bg-slate-700/40 animate-pulse"
          />
          <BokehPlot
            v-else-if="timePlot?.lc_time"
            compact
            :script="timePlot.lc_time.script"
            :div="timePlot.lc_time.div"
          />
        </div>
      </section>

      <section class="aots-panel-compact space-y-3">
        <form class="text-xs flex flex-wrap items-end gap-x-4 gap-y-2" @submit.prevent="updatePhasePlot">
          <label class="flex flex-col gap-1">
            <span class="text-slate-400">Period (hours)</span>
            <input
              v-model="formPeriod"
              type="number"
              step="any"
              class="aots-field-sm w-28"
            />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-slate-400">Phase bins size</span>
            <input
              v-model="formBinsize"
              type="number"
              min="0.0001"
              max="1"
              step="0.0001"
              class="aots-field-sm w-28"
            />
          </label>
          <button type="submit" class="aots-btn-primary text-xs">
            Phase lightcurve
          </button>
        </form>

        <div class="w-full max-w-full min-w-0 overflow-hidden">
          <div
            v-if="phaseLoading && !phasePlot?.lc_phase"
            class="h-[220px] sm:h-[320px] rounded bg-slate-700/40 animate-pulse"
          />
          <BokehPlot
            v-else-if="phasePlot?.lc_phase"
            compact
            :script="phasePlot.lc_phase.script"
            :div="phasePlot.lc_phase.div"
          />
        </div>
      </section>
    </div>

    <dialog
      v-if="headerDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-black/60 p-4 w-full max-w-none h-full max-h-none"
      @click.self="headerDialog = false"
    >
      <div class="aots-panel max-h-[90vh] w-full max-w-2xl overflow-hidden flex flex-col">
        <div class="flex justify-between items-center mb-3">
          <h2 class="font-medium">{{ lc.filetype }} header</h2>
          <button type="button" class="aots-btn-ghost text-sm" @click="headerDialog = false">
            Close
          </button>
        </div>
        <div class="overflow-y-auto text-xs font-mono">
          <p v-if="headerLoading" class="text-slate-400">Loading…</p>
          <ul v-else class="space-y-1">
            <li v-for="[key, value] in headerEntries" :key="key">
              <span class="text-slate-400">{{ key }}</span>:
              <span class="text-slate-100">{{ value }}</span>
            </li>
          </ul>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="lcEdit"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-black/60 p-4 w-full max-w-none h-full max-h-none"
      @click.self="lcEdit = false"
    >
      <div class="aots-panel w-full max-w-md">
        <h2 class="font-medium mb-3">Edit light curve</h2>
        <ul class="space-y-3 text-sm">
          <li>
            <label class="flex items-center gap-2">
              <input v-model="editValid" type="checkbox" />
              Valid
            </label>
          </li>
          <li>
            <label class="block">
              <span class="aots-label">Exposure time (s)</span>
              <input v-model="editExptime" type="text" class="aots-field" />
            </label>
          </li>
        </ul>
        <div class="flex justify-end gap-2 mt-4">
          <button type="button" class="aots-btn-ghost" @click="lcEdit = false">Cancel</button>
          <button type="button" class="aots-btn-primary" @click="saveLcEdit">Update</button>
        </div>
      </div>
    </dialog>
  </div>
</template>
