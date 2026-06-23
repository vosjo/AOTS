<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import AppButton from '@/components/AppButton.vue'
import { api, DEFAULT_PROJECT_LOGO } from '@/api/client'
import { useElementHeight } from '@/composables/useElementHeight'
import { useThemeStore } from '@/stores/theme'

/** HRD figure dimensions from dash/plotting.py plot_hrd(). */
const HRD_ASPECT = 1150 / 475

interface DashboardStats {
  nstars: number
  nstarslw: number
  nspec: number
  nspeclw: number
  nlc: number
  nlclw: number
  nanalyses: number
  nanalyseslw: number
}

interface StatCard {
  key: string
  label: string
  count: number
  delta: number
  to: string
}

interface StarmapPayload {
  n_stars: number
  colored_by_distance: boolean
  interactive: { script: string; div: string } | null
}

const route = useRoute()
const themeStore = useThemeStore()
const slug = computed(() => route.params.projectSlug as string)
const hrdParams = ref<Record<string, string>>({})

const { data, isFetching, isPending, refetch } = useQuery({
  queryKey: computed(() => ['dashboard', slug.value, themeStore.mode]),
  queryFn: async () => {
    const params = new URLSearchParams(hrdParams.value)
    params.set('theme', themeStore.mode)
    return api<{
      stats: DashboardStats
      recent_changes: Array<{ modeltype: string; date: string; user: string; label: string; created: boolean }>
      hrd: { script: string; div: string }
      hrd_form: {
        fields: string[]
        labels: Record<string, string>
        values: Record<string, string>
        choices: Record<string, [string, string][]>
      }
    }>(`/api/dash/${slug.value}/?${params}`)
  },
})

const {
  data: starmapData,
  isFetching: starmapFetching,
} = useQuery({
  queryKey: computed(() => ['dashboard-starmap', slug.value, themeStore.mode]),
  queryFn: () => api<StarmapPayload>(`/api/dash/${slug.value}/starmap/?theme=${themeStore.mode}`),
})

const statCards = computed((): StatCard[] => {
  const stats = data.value?.stats
  if (!stats) return []
  const base = `/w/${slug.value}`
  return [
    {
      key: 'systems',
      label: 'Systems',
      count: stats.nstars,
      delta: stats.nstarslw,
      to: `${base}/systems/stars/`,
    },
    {
      key: 'spectra',
      label: 'Spectra',
      count: stats.nspec,
      delta: stats.nspeclw,
      to: `${base}/observations/spectra/`,
    },
    {
      key: 'lightcurves',
      label: 'Light curves',
      count: stats.nlc,
      delta: stats.nlclw,
      to: `${base}/observations/lightcurves/`,
    },
    {
      key: 'analyses',
      label: 'Analyses',
      count: stats.nanalyses,
      delta: stats.nanalyseslw,
      to: `${base}/analysis/analyses/`,
    },
  ]
})

const form = computed(() => data.value?.hrd_form)
const hrdFormValues = reactive<Record<string, string>>({})

watch(
  data,
  (d) => {
    if (d?.hrd_form?.values) {
      Object.assign(hrdFormValues, d.hrd_form.values)
    }
  },
  { immediate: true },
)

const hrdControlsRef = ref<HTMLElement | null>(null)
const { height: hrdControlsHeight } = useElementHeight(hrdControlsRef)
const isLg = ref(false)

onMounted(() => {
  const mq = window.matchMedia('(min-width: 1024px)')
  const update = () => {
    isLg.value = mq.matches
  }
  update()
  mq.addEventListener('change', update)
  onUnmounted(() => mq.removeEventListener('change', update))
})

/** On desktop, size the plot frame to match the controls panel height. */
const hrdPlotFrameStyle = computed(() => {
  if (!isLg.value || !hrdControlsHeight.value) return undefined
  const h = hrdControlsHeight.value
  return {
    height: `${h}px`,
    maxHeight: `${h}px`,
    width: `min(100%, ${h * HRD_ASPECT}px)`,
  }
})

function updateHrd() {
  hrdParams.value = { ...hrdFormValues }
  void refetch()
}
</script>

<template>
  <div v-if="isPending" class="text-aots-muted">Loading dashboard…</div>
  <div v-else-if="data" class="min-w-0 space-y-6">
    <h1 class="text-2xl font-semibold">Dashboard</h1>

    <div class="grid grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
      <RouterLink
        v-for="card in statCards"
        :key="card.key"
        :to="card.to"
        class="group flex min-h-0 items-center justify-between gap-2 rounded-lg border border-aots bg-aots-surface/90 px-3 py-2 transition hover:border-aots-card hover:bg-aots-surface-muted/90"
      >
        <div class="min-w-0">
          <div class="truncate text-xs font-medium text-aots-muted group-hover:text-aots-muted">
            {{ card.label }}
          </div>
          <div class="text-xl font-semibold tabular-nums leading-tight text-aots-heading sm:text-2xl">
            {{ card.count }}
          </div>
        </div>
        <div
          v-if="card.delta > 0"
          class="shrink-0 text-right text-xs leading-snug text-emerald-400"
        >
          <span class="font-semibold">+{{ card.delta }}</span>
          <span class="block text-[0.65rem] font-normal text-aots-faint-extra">last week</span>
        </div>
      </RouterLink>
    </div>

    <div class="grid min-w-0 items-start gap-6 lg:grid-cols-3">
      <section class="aots-panel min-w-0">
        <div ref="hrdControlsRef" class="space-y-3">
          <h2 class="font-medium">HRD controls</h2>
          <div v-if="form" class="min-w-0 space-y-2 text-sm">
            <label v-for="field in form.fields" :key="field" class="block">
              <span class="aots-label">{{ form.labels[field] ?? field }}</span>
              <select
                v-model="hrdFormValues[field]"
                class="aots-select"
              >
                <option v-for="[val, label] in form.choices[field]" :key="String(val)" :value="val ?? ''">{{ label }}</option>
              </select>
            </label>
            <AppButton variant="primary" :disabled="isFetching" @click="updateHrd">
              Update Figure
            </AppButton>
          </div>
        </div>
      </section>

      <section class="aots-panel min-w-0 lg:col-span-2">
        <div
          class="min-w-0 overflow-hidden"
          :class="hrdPlotFrameStyle ? 'mx-auto' : ''"
          :style="hrdPlotFrameStyle"
        >
          <div v-if="isFetching && data.hrd" class="mb-2 text-xs text-aots-muted">Updating figure…</div>
          <BokehPlot v-if="data.hrd" fill :script="data.hrd.script" :div="data.hrd.div" />
        </div>
      </section>
    </div>

    <div class="grid min-w-0 gap-6 lg:grid-cols-2">
      <section class="aots-panel min-w-0">
        <h2 class="mb-2 font-medium">Starmap</h2>
        <div v-if="starmapFetching && !starmapData" class="text-sm text-aots-muted">Loading starmap…</div>
        <template v-else-if="starmapData">
          <BokehPlot
            v-if="starmapData.interactive"
            compact
            :script="starmapData.interactive.script"
            :div="starmapData.interactive.div"
          />
          <div v-else class="flex flex-col items-center gap-2 py-8 text-center text-sm text-aots-muted">
            <img :src="DEFAULT_PROJECT_LOGO" alt="" class="h-16 w-16 opacity-40" aria-hidden="true" />
            <p>No stars with coordinates to plot</p>
          </div>
          <p v-if="starmapData.interactive" class="mt-2 text-xs text-aots-faint-extra">
            Aitoff projection (galactic). Pan/zoom with the mouse; click a star to open its page.
            Export PNG via the save tool in the plot toolbar.
          </p>
        </template>
      </section>

      <section class="aots-panel">
        <h2 class="font-medium mb-2">Latest changes</h2>
        <ul class="text-sm space-y-2 max-h-64 overflow-y-auto">
          <li v-for="(c, i) in data.recent_changes" :key="i" class="border-b border-aots pb-2">
            <span class="text-aots-muted">{{ c.date.slice(0, 10) }}</span>
            {{ c.created ? 'Created' : 'Updated' }} {{ c.modeltype }} — {{ c.label }}
            <span class="text-aots-faint-extra">by {{ c.user }}</span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
