<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import AnalysesSectionNav from '@/components/AnalysesSectionNav.vue'
import AppAlert from '@/components/AppAlert.vue'
import { api, formatApiError } from '@/api/client'

interface FormChoice {
  value: string
  label: string
}

interface PlotterResponse {
  plot: { script: string; div: string }
  statistics: string
  form: {
    fields: string[]
    labels: Record<string, string>
    values: Record<string, string>
    choices: Record<string, FormChoice[]>
  }
}

const route = useRoute()
const slug = computed(() => route.params.projectSlug as string)
const queryParams = ref<Record<string, string>>({})

const { data, isFetching, isError, error } = useQuery({
  queryKey: computed(() => ['plotter', slug.value, queryParams.value]),
  queryFn: () => {
    const q = new URLSearchParams(queryParams.value)
    return api<PlotterResponse>(`/api/analysis/plotter/${slug.value}/?${q}`)
  },
})

const formValues = reactive<Record<string, string>>({})
const showRegression = ref(false)

watch(
  data,
  (d) => {
    if (d?.form?.values) {
      const { show_regression: regressionFlag, ...axisValues } = d.form.values
      Object.assign(formValues, axisValues)
      if (regressionFlag !== undefined) {
        showRegression.value = regressionFlag === '1'
      }
    }
  },
  { immediate: true },
)

function updateFigure() {
  queryParams.value = {
    ...formValues,
    show_regression: showRegression.value ? '1' : '0',
  }
}
</script>

<template>
  <div class="space-y-4">
    <AnalysesSectionNav />

    <AppAlert v-if="isError" kind="error">
      {{ formatApiError(error) }}
    </AppAlert>

    <div class="grid min-w-0 items-start gap-6 lg:grid-cols-3">
      <section v-if="data?.form" class="aots-panel min-w-0 space-y-3">
        <h2 class="font-medium text-slate-50">Plot setup</h2>
        <label v-for="field in data.form.fields" :key="field" class="block text-sm">
          <span class="aots-label">{{ data.form.labels[field] ?? field }}</span>
          <select
            v-model="formValues[field]"
            class="aots-select"
          >
            <option
              v-for="opt in data.form.choices[field] ?? []"
              :key="`${field}-${opt.value}`"
              :value="opt.value"
            >
              {{ opt.label || '(none)' }}
            </option>
          </select>
        </label>
        <label class="flex items-center gap-2 text-sm text-slate-200">
          <input
            v-model="showRegression"
            type="checkbox"
            class="size-4 rounded border-slate-500 bg-slate-700 text-sky-500 focus:ring-sky-400/40"
          />
          <span>Show regression line &amp; confidence band</span>
        </label>
        <button
          class="aots-btn-primary disabled:opacity-40"
          :disabled="isFetching"
          @click="updateFigure"
        >
          Update Figure
        </button>
        <div v-if="data.statistics" class="mt-4 text-sm text-slate-200">
          <h3 class="font-medium text-slate-50">Statistics</h3>
          <pre class="whitespace-pre-wrap">{{ data.statistics }}</pre>
        </div>
      </section>
      <section class="aots-panel min-w-0 lg:col-span-2">
        <div v-if="isFetching && !data?.plot" class="text-slate-300">Loading plot…</div>
        <BokehPlot v-else-if="data?.plot" :script="data.plot.script" :div="data.plot.div" />
      </section>
    </div>
  </div>
</template>
