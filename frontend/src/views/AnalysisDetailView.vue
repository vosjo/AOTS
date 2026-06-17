<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { BookOpen, Pencil, Star } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

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
  unit: string
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
  related_analyses: RelatedAnalysis[]
  related_by_category: RelatedByCategory[]
}

interface BokehEmbed {
  script: string
  div: string
}

const route = useRoute()
const auth = useAuthStore()
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

const { data: analysis, refetch } = useQuery({
  queryKey: computed(() => ['analysis', pk.value]),
  queryFn: () => api<AnalysisDetail>(`/api/analysis/analyses/${pk.value}/`),
})

const { data: plots } = useQuery({
  queryKey: computed(() => ['analysis-plots', pk.value]),
  queryFn: () => api<Record<string, BokehEmbed>>(`/api/analysis/analyses/${pk.value}/plots/`),
})

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
          class="text-slate-400 mb-1"
          :title="'Other analyses for the same star'"
        >
          {{ star.name }}
        </h3>
        <ul class="space-y-0.5">
          <li v-for="item in analysis.related_analyses" :key="item.pk">
            <RouterLink
              :to="`/w/${projectSlug}/analysis/analyses/${item.pk}/`"
              class="block rounded px-1 py-0.5 hover:bg-slate-700/60"
              :class="item.is_current ? 'bg-sky-900/40 text-sky-300' : ''"
            >
              <template v-if="item.is_current">— {{ item.category_label }} —</template>
              <template v-else>{{ item.category_label }} · {{ item.name }}</template>
            </RouterLink>
          </li>
        </ul>
      </div>

      <div v-if="analysis.related_by_category.length">
        <h3
          class="text-slate-400 mb-1"
          :title="'Other analyses in the same category'"
        >
          {{ analysis.category_label }}
        </h3>
        <ul class="space-y-0.5">
          <li v-for="item in analysis.related_by_category" :key="`category-${item.pk}`">
            <RouterLink
              :to="`/w/${projectSlug}/analysis/analyses/${item.pk}/`"
              class="block rounded px-1 py-0.5 hover:bg-slate-700/60"
              :class="item.is_current ? 'bg-sky-900/40 text-sky-300' : ''"
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
        <AppButton
          v-if="auth.isAuthenticated"
          variant="icon"
          class="absolute top-1 right-1"
          title="Edit analysis"
          @click="openDetailsEdit"
        >
          <Pencil class="w-4 h-4" />
        </AppButton>

        <h1 class="text-lg font-semibold m-0 w-full xl:w-auto">
          {{ pageTitle }}<span v-if="analysis.name" class="font-medium text-slate-300"> ({{ analysis.name }})</span>
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
          <BookOpen class="w-4 h-4 text-slate-400 shrink-0" />
          <AppButton
            variant="link"
            :href="analysis.reference_url"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ analysis.reference }}
          </AppButton>
        </div>

        <div class="flex items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            class="accent-sky-400 pointer-events-none"
            :checked="analysis.fit"
            tabindex="-1"
            aria-hidden="true"
          />
          <span>Fit</span>
        </div>
      </div>

      <div class="grid gap-4 xl:grid-cols-2">
        <section class="aots-panel-compact space-y-4 min-w-0 overflow-hidden">
          <div v-if="plots?.fit" class="w-full max-w-full min-w-0">
            <BokehPlot compact :script="plots.fit.script" :div="plots.fit.div" />
          </div>
          <div v-if="plots?.oc" class="w-full max-w-full min-w-0">
            <BokehPlot compact :script="plots.oc.script" :div="plots.oc.div" />
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
                  <tr v-if="!analysis.parameters.length">
                    <td colspan="4" class="text-slate-400">No data available</td>
                  </tr>
                  <tr v-for="param in analysis.parameters" :key="param.pk">
                    <th class="font-normal text-slate-200">
                      {{ param.cname }} ({{ param.unit }})
                    </th>
                    <td>{{ param.rvalue }}</td>
                    <td>{{ param.rerror }}</td>
                    <td>
                      <input
                        type="checkbox"
                        class="accent-sky-400"
                        :checked="param.valid"
                        :disabled="!auth.isAuthenticated"
                        @change="toggleParameterValid(param.pk, ($event.target as HTMLInputElement).checked)"
                      />
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
                v-if="analysis.can_edit && star"
                variant="secondary"
                size="sm"
                :disabled="deriveBusy"
                @click="deriveParameters"
              >
                {{ deriveButtonLabel }}
              </AppButton>
            </div>
            <p v-if="deriveMessage" class="text-xs text-slate-400 mb-2">{{ deriveMessage }}</p>
            <p class="text-xs text-slate-500 mb-2">
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
                    <td colspan="3" class="text-slate-400">
                      Not calculated yet
                      <template v-if="analysis.can_edit"> — use the button above</template>
                    </td>
                  </tr>
                  <tr v-for="param in analysis.derived_parameters" :key="param.pk">
                    <th class="font-normal text-slate-200">
                      {{ param.cname }} ({{ param.unit }})
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
              v-if="auth.isAuthenticated"
              variant="icon"
              class="absolute top-2 right-2"
              title="Edit note"
              @click="openNoteEdit"
            >
              <Pencil class="w-4 h-4" />
            </AppButton>
            <div class="text-sm text-slate-200 whitespace-pre-wrap pr-8">
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
                :script="plots[key].script"
                :div="plots[key].div"
              />
            </div>
          </div>
        </div>
      </section>
    </div>

    <dialog
      v-if="noteEdit"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-black/60 p-4 w-full max-w-none h-full max-h-none"
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
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-black/60 p-4 w-full max-w-none h-full max-h-none"
      @click.self="detailsEdit = false"
    >
      <div class="aots-panel w-full max-w-lg space-y-4">
        <h3 class="font-medium">Edit analysis</h3>
        <label class="block space-y-1">
          <span class="text-sm text-slate-300">Name</span>
          <textarea v-model="nameText" rows="2" class="aots-field w-full font-mono text-sm" />
        </label>
        <label class="block space-y-1">
          <span class="text-sm text-slate-300">Category</span>
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
          <input v-model="fitValue" type="checkbox" class="accent-sky-400" />
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
