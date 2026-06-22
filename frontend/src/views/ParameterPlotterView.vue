<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import AnalysesSectionNav from '@/components/AnalysesSectionNav.vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api, formatApiError } from '@/api/client'
import { useThemeStore } from '@/stores/theme'

interface FormChoice {
  value: string
  label: string
}

interface FormChoiceGroup {
  group: string
  options: FormChoice[]
}

type FormChoiceEntry = FormChoice | FormChoiceGroup

function isChoiceGroup(entry: FormChoiceEntry): entry is FormChoiceGroup {
  return 'group' in entry && Array.isArray((entry as FormChoiceGroup).options)
}

interface PlotterResponse {
  plot: { script: string; div: string }
  statistics: string
  form: {
    fields: string[]
    labels: Record<string, string>
    values: Record<string, string>
    choices: Record<string, FormChoiceEntry[]>
  }
}

const route = useRoute()
const themeStore = useThemeStore()
const slug = computed(() => route.params.projectSlug as string)
const queryParams = ref<Record<string, string>>({})

const { data, isFetching, isError, error } = useQuery({
  queryKey: computed(() => ['plotter', slug.value, queryParams.value, themeStore.mode]),
  queryFn: () => {
    const q = new URLSearchParams(queryParams.value)
    q.set('theme', themeStore.mode)
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
        <h2 class="font-medium text-aots-heading">Plot setup</h2>
        <label v-for="field in data.form.fields" :key="field" class="block text-sm">
          <span class="aots-label">{{ data.form.labels[field] ?? field }}</span>
          <select
            v-model="formValues[field]"
            class="aots-select"
          >
            <template v-for="(entry, idx) in data.form.choices[field] ?? []" :key="`${field}-${idx}`">
              <optgroup v-if="isChoiceGroup(entry)" :label="entry.group">
                <option
                  v-for="opt in entry.options"
                  :key="`${field}-${opt.value}`"
                  :value="opt.value"
                >
                  {{ opt.label }}
                </option>
              </optgroup>
              <option
                v-else
                :key="`${field}-${entry.value}`"
                :value="entry.value"
              >
                {{ entry.label || '(none)' }}
              </option>
            </template>
          </select>
        </label>
        <label class="flex items-center gap-2 text-sm text-aots">
          <input
            v-model="showRegression"
            type="checkbox"
            class="size-4 rounded border-aots bg-aots-surface-muted accent-aots ring-aots focus:ring-2"
          />
          <span>Show regression line &amp; confidence band</span>
        </label>
        <AppButton
          variant="primary"
          :disabled="isFetching"
          @click="updateFigure"
        >
          Update Figure
        </AppButton>
        <div v-if="data.statistics" class="mt-4 text-sm text-aots">
          <h3 class="font-medium text-aots-heading">Statistics</h3>
          <pre class="whitespace-pre-wrap">{{ data.statistics }}</pre>
        </div>
      </section>
      <section class="aots-panel min-w-0 lg:col-span-2">
        <div v-if="isFetching && !data?.plot" class="text-aots-muted">Loading plot…</div>
        <BokehPlot v-else-if="data?.plot" :script="data.plot.script" :div="data.plot.div" />
      </section>
    </div>
  </div>
</template>
