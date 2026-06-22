<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import AppButton from '@/components/AppButton.vue'
import { api, DEFAULT_PROJECT_LOGO, formatApiError } from '@/api/client'
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

interface StarmapPayload {
  preview_url: string | null
  full_url: string | null
  generated_at: string | null
  n_stars: number
  colored_by_distance: boolean
  can_edit: boolean
}

const route = useRoute()
const queryClient = useQueryClient()
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
    }>(`/api/dash/${slug.value}/?${params}`)
  },
})

const {
  data: starmapData,
  isFetching: starmapFetching,
  refetch: refetchStarmap,
} = useQuery({
  queryKey: computed(() => ['dashboard-starmap', slug.value]),
  queryFn: () => api<StarmapPayload>(`/api/dash/${slug.value}/starmap/`),
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
const starmapRegenerating = ref(false)
const starmapError = ref<string | null>(null)

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

function closeStarmap() {
  starmapOpen.value = false
}

function onStarmapKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closeStarmap()
  }
}

watch(starmapOpen, (open) => {
  if (open) {
    window.addEventListener('keydown', onStarmapKeydown)
  } else {
    window.removeEventListener('keydown', onStarmapKeydown)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onStarmapKeydown)
})

async function regenerateStarmap() {
  starmapError.value = null
  starmapRegenerating.value = true
  try {
    await api(`/api/dash/${slug.value}/starmap/regenerate/`, { method: 'POST' })
    await refetchStarmap()
    await queryClient.invalidateQueries({ queryKey: ['projects'] })
  } catch (error) {
    starmapError.value = formatApiError(error)
  } finally {
    starmapRegenerating.value = false
  }
}
</script>

<template>
  <div v-if="isFetching && !data" class="text-aots-muted">Loading dashboard…</div>
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
            <AppButton variant="primary" @click="updateHrd">Update Figure</AppButton>
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
      <section class="aots-panel min-w-0">
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
          <h2 class="font-medium">Starmap</h2>
          <AppButton
            v-if="starmapData?.can_edit"
            variant="secondary"
            :disabled="starmapRegenerating || starmapFetching"
            @click="regenerateStarmap"
          >
            {{ starmapRegenerating ? 'Regenerating…' : 'Regenerate' }}
          </AppButton>
        </div>
        <p v-if="starmapError" class="mb-2 text-sm text-red-400">{{ starmapError }}</p>
        <div v-if="starmapFetching && !starmapData" class="text-sm text-aots-muted">Loading starmap…</div>
        <template v-else-if="starmapData">
          <img
            v-if="starmapData.preview_url"
            :src="starmapData.preview_url"
            alt="Starmap preview"
            class="block w-full max-w-full cursor-pointer rounded object-contain"
            @click="starmapOpen = true"
          />
          <div v-else class="flex flex-col items-center gap-2 py-8 text-center text-sm text-aots-muted">
            <img :src="DEFAULT_PROJECT_LOGO" alt="" class="h-16 w-16 opacity-40" aria-hidden="true" />
            <p>No starmap yet</p>
          </div>
          <p
            v-if="starmapData.generated_at"
            class="mt-2 text-xs text-aots-faint-extra"
          >
            Generated {{ starmapData.generated_at.slice(0, 16).replace('T', ' ') }}
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

    <dialog
      v-if="starmapOpen && starmapData?.full_url"
      open
      class="fixed inset-0 z-50 bg-aots-overlay-strong p-8"
      aria-label="Full starmap"
      @click="closeStarmap"
    >
      <button
        type="button"
        class="absolute right-4 top-4 rounded border border-aots px-3 py-1 text-sm text-aots-heading hover:bg-aots-surface"
        aria-label="Close starmap"
        @click.stop="closeStarmap"
      >
        Close
      </button>
      <img
        :src="starmapData.full_url"
        alt="Full starmap"
        class="max-h-full max-w-full mx-auto"
        @click.stop
      />
    </dialog>
  </div>
</template>
