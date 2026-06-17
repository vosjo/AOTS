<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { Plus } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import DataTablePage from '@/components/DataTablePage.vue'
import AppAlert from '@/components/AppAlert.vue'
import AnalysesSectionNav from '@/components/AnalysesSectionNav.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import BulkDownloadProgress from '@/components/BulkDownloadProgress.vue'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useListFilters } from '@/composables/useListFilters'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

interface StarBrief {
  pk: number
  name: string
}

interface AnalysisRow {
  pk: number
  name: string
  note: string
  fit: boolean
  added_on: string
  category: string
  category_label: string
  category_color: string
  category_source: string
  star: StarBrief | Record<string, never>
}

interface UploadMessage {
  ok: boolean
  text: string
}

interface CategoryOption {
  value: string
  label: string
  color: string
}

const route = useRoute()
const auth = useAuthStore()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)
const bulk = useBulkDownload()
const filterOpen = ref(false)

const { filters, clearFilters } = useListFilters({
  system: '',
  name: '',
  category: '',
})

const { query, page, pageSize, selected, toggleRow, toggleAll, clearSelection } =
  useDataTablePage<AnalysisRow>({
    endpoint: '/api/analysis/analyses/',
    projectSlug,
    filters,
  })

const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])

const uploadOpen = ref(false)
const uploadFiles = ref<FileList | null>(null)
const uploadCategory = ref('')
const uploadBusy = ref(false)
const uploadMessages = ref<UploadMessage[]>([])

const { data: categoryOptions } = useQuery({
  queryKey: ['analysis-categories'],
  queryFn: () => api<{ results: CategoryOption[] }>('/api/analysis/categories/'),
})

function starOf(row: AnalysisRow): StarBrief | null {
  const star = row.star
  if (!star || !('pk' in star) || !star.pk) return null
  return star as StarBrief
}

function truncateNote(note: string) {
  if (!note) return '—'
  return note.length > 30 ? `${note.slice(0, 30)}…` : note
}

function onUploadFilesChange(event: Event) {
  uploadFiles.value = (event.target as HTMLInputElement).files
}

function resetUploadDialog() {
  uploadFiles.value = null
  uploadCategory.value = ''
  uploadMessages.value = []
}

async function uploadAnalyses() {
  if (!uploadFiles.value?.length || !projectStore.currentProject) return
  uploadBusy.value = true
  uploadMessages.value = []
  const fd = new FormData()
  for (const f of uploadFiles.value) fd.append('datafile', f)
  if (uploadCategory.value) fd.append('category', uploadCategory.value)
  try {
    const res = await api<{ messages?: [boolean, string][] }>(
      '/api/analysis/analyses/upload/',
      {
        method: 'POST',
        body: fd,
        headers: { Projectid: String(projectStore.currentProject.pk) },
      },
    )
    uploadMessages.value = (res.messages ?? []).map(([ok, text]) => ({ ok, text }))
    if (uploadMessages.value.every((m) => m.ok)) {
      uploadOpen.value = false
      resetUploadDialog()
    }
    await query.refetch()
  } catch (e) {
    uploadMessages.value = [{ ok: false, text: e instanceof Error ? e.message : String(e) }]
  } finally {
    uploadBusy.value = false
  }
}

async function deleteSelected() {
  if (!confirm('Are you sure you want to remove these Analyses?')) return
  for (const pk of selectedIds.value) {
    await api(`/api/analysis/analyses/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}
</script>

<template>
  <div class="space-y-4">
    <AnalysesSectionNav />

    <div v-if="uploadMessages.length && !uploadOpen" class="space-y-2">
      <AppAlert
        v-for="(msg, index) in uploadMessages"
        :key="index"
        :kind="msg.ok ? 'success' : 'error'"
      >
        {{ msg.text }}
      </AppAlert>
    </div>

    <DataTablePage
      hide-title
      :columns="[
        { id: 'star', header: 'System' },
        { id: 'name', header: 'Name' },
        { id: 'category', header: 'Category' },
        { id: 'note', header: 'Note' },
        { id: 'added_on', header: 'Creation date' },
      ]"
      :rows="rows"
      :count="query.data.value?.count ?? 0"
      :page="page"
      :page-size="pageSize"
      :loading="query.isFetching.value"
      :selected="selected"
      :selectable="auth.isAuthenticated"
      @update:page="page = $event"
      @update:page-size="pageSize = $event"
      @toggle-row="toggleRow"
      @toggle-all="toggleAll(rows)"
    >
      <template #actions>
        <button type="button" class="aots-btn-secondary" @click="filterOpen = true">Filters</button>
        <button
          v-if="auth.isAuthenticated"
          type="button"
          class="aots-btn-secondary inline-flex items-center gap-1.5"
          @click="uploadOpen = true"
        >
          <Plus class="w-4 h-4" />
          Add analysis(es)
        </button>
        <button
          v-if="auth.isAuthenticated"
          class="aots-btn-secondary disabled:opacity-40"
          :disabled="!selectedIds.length || bulk.busy"
          @click="bulk.start('analyses', selectedIds, projectStore.currentProject!.pk)"
        >
          Download analysis
        </button>
        <button
          v-if="auth.isAuthenticated"
          class="aots-btn-danger disabled:opacity-40"
          :disabled="!selectedIds.length"
          @click="deleteSelected"
        >
          Delete selected
        </button>
        <BulkDownloadProgress :status="bulk.status" :busy="bulk.busy" />
      </template>

      <template #cell-star="{ row }">
        <RouterLink
          v-if="starOf(row)"
          :to="`/w/${projectSlug}/systems/stars/${starOf(row)!.pk}`"
          class="text-sky-400 hover:text-sky-300"
        >
          {{ starOf(row)!.name }}
        </RouterLink>
        <span v-else class="text-slate-400">—</span>
      </template>

      <template #cell-name="{ row }">
        <RouterLink
          :to="`/w/${projectSlug}/analysis/analyses/${row.pk}/`"
          class="text-sky-400 hover:text-sky-300"
        >
          {{ row.name || '—' }}
        </RouterLink>
      </template>

      <template #cell-category="{ row }">
        <span
          class="inline-flex items-center gap-1.5"
          :class="row.category === 'unknown' ? 'text-amber-300' : ''"
          :title="row.category_source === 'auto' && row.category === 'unknown'
            ? 'Category could not be detected — please review'
            : row.category_label"
        >
          <span
            class="inline-block w-2.5 h-2.5 rounded-full shrink-0"
            :style="{ backgroundColor: row.category_color }"
          />
          {{ row.category_label }}
        </span>
      </template>

      <template #cell-note="{ row }">
        <span :title="row.note || undefined">{{ truncateNote(row.note) }}</span>
      </template>
    </DataTablePage>

    <ListFilterPanel
      :open="filterOpen"
      @close="filterOpen = false"
      @clear="clearFilters(); query.refetch()"
      @apply="filterOpen = false; query.refetch()"
    >
      <input v-model="filters.system" placeholder="System" class="aots-field" />
      <input v-model="filters.name" placeholder="Name" class="aots-field" />
      <input v-model="filters.category" placeholder="Category" class="aots-field" />
    </ListFilterPanel>

    <dialog
      v-if="uploadOpen"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-black/60 p-4 w-full max-w-none h-full max-h-none"
      @click.self="uploadOpen = false"
    >
      <div class="aots-panel w-full max-w-md">
        <h3 class="text-lg font-medium mb-1">Add analysis(es)</h3>
        <p class="text-sm text-slate-400 mb-4">Upload new analysis</p>
        <fieldset class="space-y-3">
          <legend class="text-sm text-slate-300 mb-2">Select analysis files</legend>
          <input type="file" multiple class="aots-field w-full" @change="onUploadFilesChange" />
          <label class="block text-sm text-slate-300">
            Category
            <select v-model="uploadCategory" class="aots-select w-full mt-1">
              <option value="">Derive from file</option>
              <option
                v-for="option in categoryOptions?.results ?? []"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </label>
          <p class="text-xs text-slate-500">
            Choose a category when the file type is not detected automatically
            (e.g. to create derived parameters for RV solutions).
          </p>
        </fieldset>
        <div v-if="uploadMessages.length" class="mt-3 space-y-2">
          <AppAlert
            v-for="(msg, index) in uploadMessages"
            :key="index"
            :kind="msg.ok ? 'success' : 'error'"
          >
            {{ msg.text }}
          </AppAlert>
        </div>
        <div class="flex gap-2 mt-4">
          <button
            type="button"
            class="aots-btn-primary"
            :disabled="uploadBusy || !uploadFiles?.length"
            @click="uploadAnalyses"
          >
            Upload…
          </button>
          <button
            type="button"
            class="aots-btn-ghost"
            :disabled="uploadBusy"
            @click="uploadOpen = false"
          >
            Cancel
          </button>
        </div>
      </div>
    </dialog>
  </div>
</template>
