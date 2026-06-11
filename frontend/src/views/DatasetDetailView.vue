<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { BookOpen, Pencil, Star } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
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

interface DatasetParameter {
  pk: number
  cname: string
  unit: string
  rvalue: number
  rerror: number
  valid: boolean
}

interface RelatedDataset {
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

interface DatasetDetail {
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
  parameters: DatasetParameter[]
  related_datasets: RelatedDataset[]
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

const { data: dataset, refetch } = useQuery({
  queryKey: computed(() => ['dataset', pk.value]),
  queryFn: () => api<DatasetDetail>(`/api/analysis/datasets/${pk.value}/`),
})

const { data: plots } = useQuery({
  queryKey: computed(() => ['dataset-plots', pk.value]),
  queryFn: () => api<Record<string, BokehEmbed>>(`/api/analysis/datasets/${pk.value}/plots/`),
})

const { data: categoryOptions } = useQuery({
  queryKey: ['dataset-categories'],
  queryFn: () => api<{ results: CategoryOption[] }>('/api/analysis/categories/'),
})

const star = computed(() => {
  const value = dataset.value?.star
  return value && 'pk' in value && value.pk ? (value as StarRef) : null
})

const pageTitle = computed(() => {
  if (!dataset.value) return 'Dataset'
  const starName = star.value?.name ?? '—'
  const categoryName = dataset.value.category_label ?? '—'
  return `${starName} — ${categoryName}`
})

const histPlotKeys = computed(() => {
  if (!plots.value) return []
  return Object.keys(plots.value).filter((key) => key !== 'fit' && key !== 'oc')
})

watch(dataset, (value) => {
  if (!value) return
  noteText.value = value.note || ''
  nameText.value = value.name || ''
  categoryValue.value = value.category || ''
  fitValue.value = value.fit
}, { immediate: true })

function openNoteEdit() {
  noteText.value = dataset.value?.note || ''
  noteEdit.value = true
}

function openDetailsEdit() {
  nameText.value = dataset.value?.name || ''
  categoryValue.value = dataset.value?.category || ''
  fitValue.value = dataset.value?.fit ?? true
  detailsEdit.value = true
}

async function saveNote() {
  await api(`/api/analysis/datasets/${pk.value}/`, {
    method: 'PATCH',
    body: { note: noteText.value.trim() },
  })
  noteEdit.value = false
  await refetch()
}

async function saveDetails() {
  await api(`/api/analysis/datasets/${pk.value}/`, {
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
</script>

<template>
  <div v-if="dataset" class="flex gap-4 items-start">
    <aside
      v-if="dataset.related_datasets.length || dataset.related_by_category.length"
      class="hidden xl:block w-52 shrink-0 aots-panel-compact text-xs sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto space-y-4"
    >
      <div v-if="dataset.related_datasets.length">
        <h2 class="font-medium text-sm mb-2">Related datasets</h2>
        <h3
          v-if="star"
          class="text-slate-400 mb-1"
          :title="'Other datasets for the same star'"
        >
          {{ star.name }}
        </h3>
        <ul class="space-y-0.5">
          <li v-for="item in dataset.related_datasets" :key="item.pk">
            <RouterLink
              :to="`/w/${projectSlug}/analysis/datasets/${item.pk}/`"
              class="block rounded px-1 py-0.5 hover:bg-slate-700/60"
              :class="item.is_current ? 'bg-sky-900/40 text-sky-300' : ''"
            >
              <template v-if="item.is_current">— {{ item.category_label }} —</template>
              <template v-else>{{ item.category_label }} · {{ item.name }}</template>
            </RouterLink>
          </li>
        </ul>
      </div>

      <div v-if="dataset.related_by_category.length">
        <h3
          class="text-slate-400 mb-1"
          :title="'Other datasets in the same category'"
        >
          {{ dataset.category_label }}
        </h3>
        <ul class="space-y-0.5">
          <li v-for="item in dataset.related_by_category" :key="`category-${item.pk}`">
            <RouterLink
              :to="`/w/${projectSlug}/analysis/datasets/${item.pk}/`"
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
        <button
          v-if="auth.isAuthenticated"
          type="button"
          class="absolute top-1 right-1 p-1 text-slate-300 hover:text-sky-400"
          title="Edit dataset"
          @click="openDetailsEdit"
        >
          <Pencil class="w-4 h-4" />
        </button>

        <h1 class="text-lg font-semibold m-0 w-full xl:w-auto">
          {{ pageTitle }}<span v-if="dataset.name" class="font-medium text-slate-300"> ({{ dataset.name }})</span>
        </h1>

        <div v-if="star" class="flex items-center gap-1.5">
          <Star class="w-4 h-4 text-amber-400 shrink-0" />
          <RouterLink
            :to="`/w/${projectSlug}/systems/stars/${star.pk}`"
            class="font-medium text-sky-400 hover:text-sky-300"
          >
            {{ star.name }}
          </RouterLink>
        </div>

        <div class="flex items-center gap-1.5 text-sm">
          <span
            class="inline-flex items-center gap-1.5"
            :class="dataset.category === 'unknown' ? 'text-amber-300' : ''"
          >
            <span
              class="inline-block w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ backgroundColor: dataset.category_color }"
            />
            {{ dataset.category_label }}
          </span>
        </div>

        <div v-if="dataset.reference" class="flex items-center gap-1.5 text-sm">
          <BookOpen class="w-4 h-4 text-slate-400 shrink-0" />
          <a
            :href="dataset.reference_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-sky-400 hover:text-sky-300"
          >
            {{ dataset.reference }}
          </a>
        </div>

        <div class="flex items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            class="accent-sky-400 pointer-events-none"
            :checked="dataset.fit"
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
                  <tr v-if="!dataset.parameters.length">
                    <td colspan="4" class="text-slate-400">No data available</td>
                  </tr>
                  <tr v-for="param in dataset.parameters" :key="param.pk">
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

          <section class="aots-panel-compact relative">
            <h2 class="text-sm font-medium mb-2">Notes</h2>
            <button
              v-if="auth.isAuthenticated"
              type="button"
              class="absolute top-2 right-2 p-1 text-slate-300 hover:text-sky-400"
              title="Edit note"
              @click="openNoteEdit"
            >
              <Pencil class="w-4 h-4" />
            </button>
            <div class="text-sm text-slate-200 whitespace-pre-wrap pr-8">
              {{ dataset.note || '—' }}
            </div>
          </section>

          <section class="aots-panel-compact">
            <h2 class="text-sm font-medium mb-2">Meta data</h2>
            <table class="aots-kv-table">
              <tbody>
                <tr>
                  <th>Added by</th>
                  <td>{{ dataset.added_by }}</td>
                </tr>
                <tr>
                  <th>Added on</th>
                  <td>{{ dataset.added_on }}</td>
                </tr>
                <tr>
                  <th>Last modified</th>
                  <td>{{ dataset.last_modified }}</td>
                </tr>
                <tr>
                  <th>Modified by</th>
                  <td>{{ dataset.modified_by }}</td>
                </tr>
                <tr v-if="dataset.file_type">
                  <th>File type</th>
                  <td>{{ dataset.file_type }}</td>
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
          <button type="button" class="aots-btn-primary" @click="saveNote">Update</button>
          <button type="button" class="aots-btn-ghost" @click="noteEdit = false">Cancel</button>
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
        <h3 class="font-medium">Edit dataset</h3>
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
          <span>Fit (dataset contains fit results)</span>
        </label>
        <div class="flex gap-2">
          <button type="button" class="aots-btn-primary" @click="saveDetails">Update</button>
          <button type="button" class="aots-btn-ghost" @click="detailsEdit = false">Cancel</button>
        </div>
      </div>
    </dialog>
  </div>
</template>
