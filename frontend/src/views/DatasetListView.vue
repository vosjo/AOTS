<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import DataTablePage from '@/components/DataTablePage.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
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

interface MethodBrief {
  pk: number
  name: string
  description: string
}

interface DatasetRow {
  pk: number
  name: string
  note: string
  valid: boolean
  added_on: string
  star: StarBrief | Record<string, never>
  method: MethodBrief | Record<string, never>
}

interface UploadMessage {
  ok: boolean
  text: string
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
  method: '',
})

const { query, page, pageSize, selected, toggleRow, toggleAll, clearSelection } =
  useDataTablePage<DatasetRow>({
    endpoint: '/api/analysis/datasets/',
    projectSlug,
    filters,
  })

const rows = computed(() => query.data.value?.results ?? [])
const selectedIds = computed(() => [...selected.value])

const uploadOpen = ref(false)
const uploadFiles = ref<FileList | null>(null)
const uploadBusy = ref(false)
const uploadMessages = ref<UploadMessage[]>([])

function starOf(row: DatasetRow): StarBrief | null {
  const star = row.star
  if (!star || !('pk' in star) || !star.pk) return null
  return star as StarBrief
}

function methodOf(row: DatasetRow): MethodBrief | null {
  const method = row.method
  if (!method || !('pk' in method) || !method.pk) return null
  return method as MethodBrief
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
  uploadMessages.value = []
}

async function uploadDatasets() {
  if (!uploadFiles.value?.length || !projectStore.currentProject) return
  uploadBusy.value = true
  uploadMessages.value = []
  const fd = new FormData()
  for (const f of uploadFiles.value) fd.append('datafile', f)
  try {
    const res = await api<{ messages?: [boolean, string][] }>(
      `/w/${projectSlug.value}/analysis/datasets/`,
      { method: 'POST', body: fd },
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
  if (!confirm('Are you sure you want to remove these DataSets?')) return
  for (const pk of selectedIds.value) {
    await api(`/api/analysis/datasets/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}
</script>

<template>
  <div class="space-y-4">
    <ul v-if="uploadMessages.length && !uploadOpen" class="space-y-2">
      <li
        v-for="(msg, index) in uploadMessages"
        :key="index"
        class="rounded-md border px-3 py-2 text-sm"
        :class="msg.ok
          ? 'border-emerald-500/40 bg-emerald-950/40 text-emerald-100'
          : 'border-red-500/40 bg-red-950/40 text-red-100'"
      >
        {{ msg.text }}
      </li>
    </ul>

    <DataTablePage
      title="Datasets"
      :columns="[
        { id: 'star', header: 'System' },
        { id: 'name', header: 'Name' },
        { id: 'note', header: 'Note' },
        { id: 'method', header: 'Method' },
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
          Add dataset(s)
        </button>
        <button
          v-if="auth.isAuthenticated"
          class="aots-btn-secondary disabled:opacity-40"
          :disabled="!selectedIds.length || bulk.busy"
          @click="bulk.start('datasets', selectedIds, projectStore.currentProject!.pk)"
        >
          Download dataset
        </button>
        <button
          v-if="auth.isAuthenticated"
          class="aots-btn-danger disabled:opacity-40"
          :disabled="!selectedIds.length"
          @click="deleteSelected"
        >
          Delete selected
        </button>
        <span v-if="bulk.status" class="text-xs text-slate-400">{{ bulk.status }}</span>
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
          :to="`/w/${projectSlug}/analysis/datasets/${row.pk}/`"
          class="text-sky-400 hover:text-sky-300"
        >
          {{ row.name || '—' }}
        </RouterLink>
      </template>

      <template #cell-note="{ row }">
        <span :title="row.note || undefined">{{ truncateNote(row.note) }}</span>
      </template>

      <template #cell-method="{ row }">
        <span v-if="methodOf(row)" :title="methodOf(row)!.description">
          {{ methodOf(row)!.name }}
        </span>
        <span v-else class="text-slate-400">—</span>
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
      <input v-model="filters.method" placeholder="Method" class="aots-field" />
    </ListFilterPanel>

    <dialog
      v-if="uploadOpen"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-black/60 p-4 w-full max-w-none h-full max-h-none"
      @click.self="uploadOpen = false"
    >
      <div class="aots-panel w-full max-w-md">
        <h3 class="text-lg font-medium mb-1">Add dataset(s)</h3>
        <p class="text-sm text-slate-400 mb-4">Upload new dataset</p>
        <fieldset class="space-y-3">
          <legend class="text-sm text-slate-300 mb-2">Select dataset files</legend>
          <input type="file" multiple class="aots-field w-full" @change="onUploadFilesChange" />
        </fieldset>
        <ul v-if="uploadMessages.length" class="mt-3 space-y-2">
          <li
            v-for="(msg, index) in uploadMessages"
            :key="index"
            class="rounded-md border px-3 py-2 text-sm"
            :class="msg.ok
              ? 'border-emerald-500/40 bg-emerald-950/40 text-emerald-100'
              : 'border-red-500/40 bg-red-950/40 text-red-100'"
          >
            {{ msg.text }}
          </li>
        </ul>
        <div class="flex gap-2 mt-4">
          <button
            type="button"
            class="aots-btn-primary"
            :disabled="uploadBusy || !uploadFiles?.length"
            @click="uploadDatasets"
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
