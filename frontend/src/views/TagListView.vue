<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Pencil, Plus, Trash2 } from 'lucide-vue-next'
import DataTablePage from '@/components/DataTablePage.vue'
import SystemsSectionNav from '@/components/SystemsSectionNav.vue'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

interface TagRow {
  pk: number
  name: string
  description: string
  color: string
}

const DEFAULT_COLOR = '#8B0000'

const route = useRoute()
const projectSlug = computed(() => route.params.projectSlug as string)
const auth = useAuthStore()
const projectStore = useProjectStore()

const { query, page, pageSize, selected, toggleRow, toggleAll } = useDataTablePage<TagRow>({
  endpoint: '/api/systems/tags/',
  projectSlug,
})
const rows = computed(() => query.data.value?.results ?? [])

const columns = computed(() => {
  const cols = [
    { id: 'name', header: 'Name' },
    { id: 'description', header: 'Description' },
    { id: 'color', header: 'Color' },
  ]
  if (auth.isAuthenticated) cols.push({ id: 'actions', header: 'Action' })
  return cols
})

const dialogOpen = ref(false)
const editingPk = ref<number | null>(null)
const formName = ref('')
const formDescription = ref('')
const formColor = ref(DEFAULT_COLOR)
const saving = ref(false)
const formError = ref<string | null>(null)

const dialogTitle = computed(() => (editingPk.value === null ? 'Add new tag' : 'Edit tag'))
const saveLabel = computed(() => (editingPk.value === null ? 'Add' : 'Update'))

function openAdd() {
  editingPk.value = null
  formName.value = ''
  formDescription.value = ''
  formColor.value = DEFAULT_COLOR
  formError.value = null
  dialogOpen.value = true
}

function openEdit(row: TagRow) {
  editingPk.value = row.pk
  formName.value = row.name
  formDescription.value = row.description ?? ''
  formColor.value = row.color
  formError.value = null
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  editingPk.value = null
}

async function saveTag() {
  const project = projectStore.currentProject
  if (!project) return
  saving.value = true
  formError.value = null
  try {
    const body = {
      name: formName.value,
      description: formDescription.value,
      color: formColor.value,
    }
    if (editingPk.value === null) {
      await api('/api/systems/tags/', {
        method: 'POST',
        body: { ...body, project: project.pk },
      })
    } else {
      await api(`/api/systems/tags/${editingPk.value}/`, {
        method: 'PATCH',
        body,
      })
    }
    closeDialog()
    await query.refetch()
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

async function deleteTag(row: TagRow) {
  if (!confirm('Are you sure you want to remove this Tag?')) return
  await api(`/api/systems/tags/${row.pk}/`, { method: 'DELETE' })
  await query.refetch()
}
</script>

<template>
  <div class="space-y-4">
    <SystemsSectionNav />

    <DataTablePage
      hide-title
    :columns="columns"
    :rows="rows"
    :count="query.data.value?.count ?? 0"
    :page="page"
    :page-size="pageSize"
    :loading="query.isFetching.value"
    :selected="selected"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
    @toggle-row="toggleRow"
    @toggle-all="toggleAll(rows)"
  >
    <template v-if="auth.isAuthenticated" #actions>
      <button type="button" class="aots-btn-primary inline-flex items-center gap-1.5" @click="openAdd">
        <Plus class="w-4 h-4" />
        Add tag
      </button>
    </template>

    <template #cell-description="{ row }">
      <span class="text-slate-300">{{ row.description || '—' }}</span>
    </template>

    <template #cell-color="{ row }">
      <span class="inline-flex items-center gap-2 font-mono text-sm">
        <i
          class="inline-block w-3 h-3 rounded-full shrink-0 border border-slate-500"
          :style="{ backgroundColor: row.color }"
        />
        {{ row.color }}
      </span>
    </template>

    <template v-if="auth.isAuthenticated" #cell-actions="{ row }">
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="p-1 text-slate-300 hover:text-sky-400"
          title="Edit tag"
          @click="openEdit(row)"
        >
          <Pencil class="w-4 h-4" />
        </button>
        <button
          type="button"
          class="p-1 text-slate-300 hover:text-red-400"
          title="Delete tag"
          @click="deleteTag(row)"
        >
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </template>
  </DataTablePage>

  <dialog
    v-if="dialogOpen"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-black/60 p-4 w-full max-w-none h-full max-h-none"
    @click.self="closeDialog"
  >
    <div class="aots-panel w-full max-w-md">
      <h3 class="font-medium mb-4">{{ dialogTitle }}</h3>
      <div class="space-y-3">
        <input
          v-model="formName"
          type="text"
          class="aots-field w-full"
          placeholder="Name"
          maxlength="75"
        />
        <textarea
          v-model="formDescription"
          class="aots-field w-full"
          placeholder="Description"
          rows="2"
        />
        <div class="flex items-center gap-3">
          <label class="text-sm text-slate-300 shrink-0">Color</label>
          <input v-model="formColor" type="color" class="h-9 w-14 cursor-pointer rounded border border-slate-500 bg-transparent" />
          <span class="font-mono text-sm text-slate-300">{{ formColor }}</span>
        </div>
        <p v-if="formError" class="text-sm text-red-400">{{ formError }}</p>
      </div>
      <div class="flex gap-2 mt-4">
        <button type="button" class="aots-btn-primary" :disabled="saving" @click="saveTag">
          {{ saveLabel }}
        </button>
        <button type="button" class="aots-btn-ghost" :disabled="saving" @click="closeDialog">
          Cancel
        </button>
      </div>
    </div>
  </dialog>
  </div>
</template>
