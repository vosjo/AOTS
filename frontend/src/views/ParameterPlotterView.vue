<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'

interface FormChoice {
  value: string
  label: string
}

interface PlotterResponse {
  plot: { script: string; div: string }
  statistics: string
  form: {
    fields: string[]
    values: Record<string, string>
    choices: Record<string, FormChoice[]>
  }
}

const route = useRoute()
const slug = computed(() => route.params.projectSlug as string)
const queryParams = reactive<Record<string, string>>({})

const { data, refetch, isFetching } = useQuery({
  queryKey: computed(() => ['plotter', slug.value, { ...queryParams }]),
  queryFn: () => {
    const q = new URLSearchParams(queryParams)
    return api<PlotterResponse>(`/api/analysis/plotter/${slug.value}/?${q}`)
  },
})

const formValues = reactive<Record<string, string>>({})

watch(
  data,
  (d) => {
    if (d?.form?.values) {
      Object.assign(formValues, d.form.values)
    }
  },
  { immediate: true },
)

function updateFigure() {
  Object.assign(queryParams, formValues)
  refetch()
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold">Parameter plotter</h1>
    <div class="grid gap-6 lg:grid-cols-3">
      <section v-if="data?.form" class="aots-panel space-y-3">
        <h2 class="font-medium text-slate-50">Plot setup</h2>
        <label v-for="field in data.form.fields" :key="field" class="block text-sm">
          <span class="aots-label capitalize">{{ field }}</span>
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
      <section class="aots-panel lg:col-span-2">
        <BokehPlot v-if="data?.plot" :script="data.plot.script" :div="data.plot.div" />
      </section>
    </div>
  </div>
</template>
