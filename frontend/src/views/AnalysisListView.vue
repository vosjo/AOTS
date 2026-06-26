<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { Plus } from '@lucide/vue'
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import DataTablePage from '@/components/DataTablePage.vue'
import AppAlert from '@/components/AppAlert.vue'
import AnalysesSectionNav from '@/components/AnalysesSectionNav.vue'
import ListFilterPanel from '@/components/ListFilterPanel.vue'
import BulkDownloadProgress from '@/components/BulkDownloadProgress.vue'
import { confirmAction } from '@/composables/useConfirm'
import { useBulkDownload } from '@/composables/useBulkDownload'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'
import { useListFilters } from '@/composables/useListFilters'
import { api, formatApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useProjectPermissions } from '@/composables/useProjectPermissions'

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
const { canAdd } = useProjectPermissions()
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
const { emptyMessage } = useEmptyTableMessage({ query, filters, entity: 'analyses' })

const uploadOpen = ref(false)
const uploadFiles = ref<FileList | null>(null)
const uploadCategory = ref('')
const uploadBusy = ref(false)
const uploadMessages = ref<UploadMessage[]>([])

const categoryDialog = ref(false)
const bulkCategory = ref('')
const categoryError = ref('')
const categoryBusy = ref(false)

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
  if (!(await confirmAction({
    title: 'Remove analyses',
    message: 'Are you sure you want to remove these analyses?',
    confirmLabel: 'Remove',
  }))) return
  for (const pk of selectedIds.value) {
    await api(`/api/analysis/analyses/${pk}/`, { method: 'DELETE' })
  }
  clearSelection()
  await query.refetch()
}

function openCategoryDialog() {
  bulkCategory.value = ''
  categoryError.value = ''
  categoryDialog.value = true
}

async function applyCategory() {
  if (!bulkCategory.value) {
    categoryError.value = 'Select a category.'
    return
  }
  categoryBusy.value = true
  categoryError.value = ''
  try {
    for (const pk of selectedIds.value) {
      await api(`/api/analysis/analyses/${pk}/`, {
        method: 'PATCH',
        body: {
          category: bulkCategory.value,
          category_source: 'user',
        },
      })
    }
    categoryDialog.value = false
    clearSelection()
    await query.refetch()
  } catch (e) {
    categoryError.value = formatApiError(e)
  } finally {
    categoryBusy.value = false
  }
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
      :empty-message="emptyMessage"
      :selected="selected"
      :selectable="auth.isAuthenticated"
      @update:page="page = $event"
      @update:page-size="pageSize = $event"
      @toggle-row="toggleRow"
      @toggle-all="toggleAll(rows)"
    >
      <template #actions>
        <AppButton variant="secondary" @click="filterOpen = true">Filters</AppButton>
        <AppButton
          v-if="canAdd"
          variant="primary"
          class="inline-flex items-center gap-1.5"
          @click="uploadOpen = true"
        >
          <Plus class="w-4 h-4" />
          Upload analysis(es)
        </AppButton>
        <AppButton
          v-if="canAdd"
          variant="secondary"
          :disabled="!selectedIds.length || categoryBusy"
          @click="openCategoryDialog"
        >
          Set category
        </AppButton>
        <AppButton
          v-if="auth.isAuthenticated"
          variant="secondary"
          :disabled="!selectedIds.length || bulk.busy"
          @click="bulk.start('analyses', selectedIds, projectStore.currentProject!.pk)"
        >
          Download analysis
        </AppButton>
        <AppButton
          v-if="canAdd"
          variant="danger"
          :disabled="!selectedIds.length"
          @click="deleteSelected"
        >
          Delete selected
        </AppButton>
        <BulkDownloadProgress :status="bulk.status" :busy="bulk.busy" />
      </template>

      <template #cell-star="{ row }">
        <AppButton
          v-if="starOf(row)"
          variant="link"
          :to="`/w/${projectSlug}/systems/stars/${starOf(row)!.pk}`"
        >
          {{ starOf(row)!.name }}
        </AppButton>
        <span v-else class="text-aots-muted">—</span>
      </template>

      <template #cell-name="{ row }">
        <AppButton
          variant="link"
          :to="`/w/${projectSlug}/analysis/analyses/${row.pk}/`"
        >
          {{ row.name || '—' }}
        </AppButton>
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
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="uploadOpen = false"
    >
      <div class="aots-panel w-full max-w-md">
        <h3 class="text-lg font-medium mb-1">Add analysis(es)</h3>
        <p class="text-sm text-aots-muted mb-4">Upload new analysis</p>
        <fieldset class="space-y-3">
          <legend class="text-sm text-aots-muted mb-2">Select analysis files</legend>
          <input type="file" multiple class="aots-field w-full" @change="onUploadFilesChange" />
          <label class="block text-sm text-aots-muted">
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
          <p class="text-xs text-aots-faint-extra">
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
          <AppButton
            variant="primary"
            :disabled="uploadBusy || !uploadFiles?.length"
            @click="uploadAnalyses"
          >
            Upload…
          </AppButton>
          <AppButton
            variant="ghost"
            :disabled="uploadBusy"
            @click="uploadOpen = false"
          >
            Cancel
          </AppButton>
        </div>
      </div>
    </dialog>

    <dialog
      v-if="categoryDialog"
      open
      class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
      @click.self="categoryDialog = false"
    >
      <div class="aots-panel w-full max-w-md">
        <h3 class="font-medium mb-1">Set category</h3>
        <p class="text-sm text-aots-muted mb-4">
          Apply a category to {{ selectedIds.length }} selected analysis(es).
        </p>
        <label class="block text-sm text-aots-muted">
          Category
          <select v-model="bulkCategory" class="aots-select w-full mt-1">
            <option value="">Select category…</option>
            <option
              v-for="option in categoryOptions?.results ?? []"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>
        <AppAlert v-if="categoryError" kind="error" class="mt-3">{{ categoryError }}</AppAlert>
        <div class="flex gap-2 mt-4">
          <AppButton
            variant="primary"
            :disabled="categoryBusy || !bulkCategory"
            @click="applyCategory"
          >
            Apply
          </AppButton>
          <AppButton variant="ghost" :disabled="categoryBusy" @click="categoryDialog = false">
            Cancel
          </AppButton>
        </div>
      </div>
    </dialog>
  </div>
</template>
