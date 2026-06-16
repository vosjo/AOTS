<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'
import { useElementHeight } from '@/composables/useElementHeight'

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

const route = useRoute()
const slug = computed(() => route.params.projectSlug as string)
const hrdParams = ref<Record<string, string>>({})

const { data, isFetching, refetch } = useQuery({
  queryKey: computed(() => ['dashboard', slug.value, hrdParams.value]),
  queryFn: async () => {
    const params = new URLSearchParams(hrdParams.value)
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
      starmap: { preview_url: string | null; full_url: string | null }
    }>(`/api/dash/${slug.value}/?${params}`)
  },
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
const starmapOpen = ref(false)

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
  refetch()
}
</script>

<template>
  <div v-if="isFetching && !data" class="text-slate-300">Loading dashboard…</div>
  <div v-else-if="data" class="min-w-0 space-y-6">
    <h1 class="text-2xl font-semibold">Dashboard</h1>

    <div class="grid grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
      <RouterLink
        v-for="card in statCards"
        :key="card.key"
        :to="card.to"
        class="group flex min-h-0 items-center justify-between gap-2 rounded-lg border border-slate-600 bg-slate-800/90 px-3 py-2 transition hover:border-sky-500/70 hover:bg-slate-700/90"
      >
        <div class="min-w-0">
          <div class="truncate text-xs font-medium text-slate-400 group-hover:text-slate-300">
            {{ card.label }}
          </div>
          <div class="text-xl font-semibold tabular-nums leading-tight text-slate-50 sm:text-2xl">
            {{ card.count }}
          </div>
        </div>
        <div
          v-if="card.delta > 0"
          class="shrink-0 text-right text-xs leading-snug text-emerald-400"
        >
          <span class="font-semibold">+{{ card.delta }}</span>
          <span class="block text-[0.65rem] font-normal text-slate-500">last week</span>
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
            <button class="aots-btn-primary" @click="updateHrd">Update Figure</button>
          </div>
        </div>
      </section>

      <section class="aots-panel min-w-0 lg:col-span-2">
        <div
          class="min-w-0 overflow-hidden"
          :class="hrdPlotFrameStyle ? 'mx-auto' : ''"
          :style="hrdPlotFrameStyle"
        >
          <BokehPlot v-if="data.hrd" fill :script="data.hrd.script" :div="data.hrd.div" />
        </div>
      </section>
    </div>

    <div class="grid min-w-0 gap-6 lg:grid-cols-2">
      <section v-if="data.starmap.preview_url" class="aots-panel min-w-0">
        <h2 class="font-medium mb-2">Starmap</h2>
        <img
          :src="data.starmap.preview_url"
          alt="Starmap preview"
          class="block w-full max-w-full cursor-pointer rounded object-contain"
          @click="starmapOpen = true"
        />
      </section>

      <section class="aots-panel">
        <h2 class="font-medium mb-2">Latest changes</h2>
        <ul class="text-sm space-y-2 max-h-64 overflow-y-auto">
          <li v-for="(c, i) in data.recent_changes" :key="i" class="border-b border-slate-600 pb-2">
            <span class="text-slate-300">{{ c.date.slice(0, 10) }}</span>
            {{ c.created ? 'Created' : 'Updated' }} {{ c.modeltype }} — {{ c.label }}
            <span class="text-slate-500">by {{ c.user }}</span>
          </li>
        </ul>
      </section>
    </div>

    <dialog v-if="starmapOpen && data.starmap.full_url" open class="fixed inset-0 z-50 bg-black/80 p-8" @click="starmapOpen = false">
      <img :src="data.starmap.full_url" alt="Full starmap" class="max-h-full max-w-full mx-auto" @click.stop />
    </dialog>
  </div>
</template>
