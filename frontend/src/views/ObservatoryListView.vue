<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { CheckCircle2, Pencil, Plus, Trash2, XCircle } from '@lucide/vue'
import DataTablePage from '@/components/DataTablePage.vue'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import ObservatoryWorldMap from '@/components/ObservatoryWorldMap.vue'
import { confirmAction } from '@/composables/useConfirm'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'
import { api, type PaginatedResponse } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useProjectPermissions } from '@/composables/useProjectPermissions'

interface ObservatoryRow {
  pk: number
  name: string
  short_name: string
  telescopes: string
  latitude: number
  longitude: number
  altitude: number
  space_craft: boolean
  note: string
  url: string
  weatherurl: string
}

interface ObservatoryForm {
  name: string
  short_name: string
  telescopes: string
  latitude: string
  longitude: string
  altitude: string
  space_craft: boolean
  note: string
  url: string
  weatherurl: string
}

const emptyForm = (): ObservatoryForm => ({
  name: '',
  short_name: '',
  telescopes: '',
  latitude: '0',
  longitude: '0',
  altitude: '0',
  space_craft: false,
  note: '',
  url: '',
  weatherurl: '',
})

const route = useRoute()
const projectSlug = computed(() => route.params.projectSlug as string)
const auth = useAuthStore()
const { canAdd } = useProjectPermissions()
const projectStore = useProjectStore()

const { query, page, pageSize, selected, toggleRow, toggleAll } = useDataTablePage<ObservatoryRow>({
  endpoint: '/api/observations/observatories/',
  projectSlug,
})
const rows = computed(() => query.data.value?.results ?? [])
const { emptyMessage } = useEmptyTableMessage({ query, entity: 'observatories' })

const mapQuery = useQuery({
  queryKey: computed(() => ['observatories-map', projectStore.currentProject?.pk]),
  queryFn: async () => {
    const project = projectStore.currentProject
    if (!project) return { count: 0, next: null, previous: null, results: [] as ObservatoryRow[] }
    const params = new URLSearchParams({
      project: String(project.pk),
      page_size: '1000',
    })
    return api<PaginatedResponse<ObservatoryRow>>(`/api/observations/observatories/?${params}`)
  },
  enabled: computed(() => !!projectStore.currentProject),
})

const groundObservatories = computed(() =>
  (mapQuery.data.value?.results ?? []).filter((row) => !row.space_craft),
)

async function refreshObservatories() {
  await Promise.all([query.refetch(), mapQuery.refetch()])
}

const columns = computed(() => {
  const cols = [
    { id: 'name', header: 'Name' },
    { id: 'telescopes', header: 'Telescopes' },
    { id: 'latitude', header: 'Latitude (deg)' },
    { id: 'longitude', header: 'Longitude (deg)' },
    { id: 'altitude', header: 'Altitude (m)' },
    { id: 'space_craft', header: 'Space craft' },
    { id: 'note', header: 'Note' },
  ]
  if (canAdd.value) cols.push({ id: 'actions', header: 'Action' })
  return cols
})

const NOTE_COLLAPSE_CHARS = 60

const expandedNoteIds = ref(new Set<number>())
const dialogOpen = ref(false)
const editingPk = ref<number | null>(null)
const form = ref<ObservatoryForm>(emptyForm())
const saving = ref(false)
const formError = ref<string | null>(null)

const dialogTitle = computed(() =>
  editingPk.value === null ? 'Add a new observatory' : 'Edit observatory data',
)
const saveLabel = computed(() => (editingPk.value === null ? 'Add' : 'Update'))

function observatoryHref(url: string) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return `http://${url}`
}

function formatCoord(value: number) {
  return Math.round(value * 1000) / 1000
}

function formatAltitude(value: number) {
  return Math.round(value)
}

function noteNeedsToggle(note: string) {
  const text = note.trim()
  return text.length > NOTE_COLLAPSE_CHARS || text.includes('\n')
}

function isNoteExpanded(pk: number) {
  return expandedNoteIds.value.has(pk)
}

function toggleNote(pk: number) {
  const next = new Set(expandedNoteIds.value)
  if (next.has(pk)) next.delete(pk)
  else next.add(pk)
  expandedNoteIds.value = next
}

function openAdd() {
  editingPk.value = null
  form.value = emptyForm()
  formError.value = null
  dialogOpen.value = true
}

function openEdit(row: ObservatoryRow) {
  editingPk.value = row.pk
  form.value = {
    name: row.name,
    short_name: row.short_name ?? '',
    telescopes: row.telescopes ?? '',
    latitude: String(row.latitude ?? 0),
    longitude: String(row.longitude ?? 0),
    altitude: String(row.altitude ?? 0),
    space_craft: row.space_craft,
    note: row.note ?? '',
    url: row.url ?? '',
    weatherurl: row.weatherurl ?? '',
  }
  formError.value = null
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  editingPk.value = null
}

function formBody() {
  return {
    name: form.value.name,
    short_name: form.value.short_name,
    telescopes: form.value.telescopes,
    latitude: parseFloat(form.value.latitude) || 0,
    longitude: parseFloat(form.value.longitude) || 0,
    altitude: parseFloat(form.value.altitude) || 0,
    space_craft: form.value.space_craft,
    note: form.value.note,
    url: form.value.url,
    weatherurl: form.value.weatherurl,
  }
}

async function saveObservatory() {
  const project = projectStore.currentProject
  if (!project) return
  saving.value = true
  formError.value = null
  try {
    const body = formBody()
    if (editingPk.value === null) {
      await api('/api/observations/observatories/', {
        method: 'POST',
        body: { ...body, project: project.pk },
      })
    } else {
      await api(`/api/observations/observatories/${editingPk.value}/`, {
        method: 'PATCH',
        body,
      })
    }
    closeDialog()
    await refreshObservatories()
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

async function deleteObservatory(row: ObservatoryRow) {
  if (!(await confirmAction({
    title: 'Delete observatory',
    message: 'Are you sure you want to delete this observatory? This cannot be undone.',
  }))) return
  try {
    await api(`/api/observations/observatories/${row.pk}/`, { method: 'DELETE' })
    await refreshObservatories()
  } catch (e) {
    const status = (e as { statusCode?: number })?.statusCode
    if (status === 500) {
      alert('Observatory can not be deleted, since spectra still refer to it.')
    }
  }
}
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-semibold text-aots-heading">Observatories</h1>

    <div class="grid min-w-0 items-start gap-6 lg:grid-cols-2">
      <div class="min-w-0">
        <DataTablePage
          hide-title
          :columns="columns"
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
    <template v-if="canAdd" #actions>
      <AppButton variant="primary" class="inline-flex items-center gap-1.5" @click="openAdd">
        <Plus class="w-4 h-4" />
        Add observatory
      </AppButton>
    </template>

    <template #cell-name="{ row }">
      <AppButton
        v-if="row.url"
        variant="link"
        :href="observatoryHref(row.url)"
        target="_blank"
        rel="noopener"
      >
        {{ row.name }}
      </AppButton>
      <span v-else>{{ row.name }}</span>
    </template>

    <template #cell-latitude="{ row }">{{ formatCoord(row.latitude) }}</template>
    <template #cell-longitude="{ row }">{{ formatCoord(row.longitude) }}</template>
    <template #cell-altitude="{ row }">{{ formatAltitude(row.altitude) }}</template>

    <template #cell-space_craft="{ row }">
      <CheckCircle2 v-if="row.space_craft" class="w-4 h-4 text-emerald-400" title="Space craft" />
      <XCircle v-else class="w-4 h-4 text-red-400" title="Ground-based" />
    </template>

    <template #cell-note="{ row }">
      <div
        class="min-w-0"
        :class="isNoteExpanded(row.pk) ? 'max-w-md' : 'max-w-[14rem]'"
      >
        <template v-if="!row.note?.trim()">
          <span class="text-aots-muted">—</span>
        </template>
        <template v-else>
          <p
            class="break-words whitespace-pre-wrap text-aots-muted"
            :class="{ 'line-clamp-2': !isNoteExpanded(row.pk) && noteNeedsToggle(row.note) }"
          >
            {{ row.note }}
          </p>
          <AppButton
            v-if="noteNeedsToggle(row.note)"
            variant="link"
            size="sm"
            class="mt-0.5 p-0 text-xs"
            @click="toggleNote(row.pk)"
          >
            {{ isNoteExpanded(row.pk) ? 'Hide' : 'Show note' }}
          </AppButton>
        </template>
      </div>
    </template>

    <template v-if="canAdd" #cell-actions="{ row }">
      <div class="flex items-center gap-2">
        <AppButton
          variant="icon"
          title="Edit observatory"
          @click="openEdit(row)"
        >
          <Pencil class="w-4 h-4" />
        </AppButton>
        <AppButton
          variant="icon-danger"
          title="Delete observatory"
          @click="deleteObservatory(row)"
        >
          <Trash2 class="w-4 h-4" />
        </AppButton>
      </div>
        </template>
        </DataTablePage>
      </div>

      <section class="aots-panel min-w-0 self-start lg:sticky lg:top-20">
        <h2 class="mb-3 font-medium text-aots-heading">Ground observatories</h2>
        <ObservatoryWorldMap :observatories="groundObservatories" />
      </section>
    </div>
  </div>

  <dialog
    v-if="dialogOpen"
    open
    class="fixed inset-0 z-50 m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    @click.self="closeDialog"
  >
    <div class="aots-panel w-full max-w-lg max-h-[90vh] overflow-y-auto">
      <h3 class="font-medium mb-4">{{ dialogTitle }}</h3>
      <div class="space-y-3 text-sm">
        <label class="block">
          <span class="aots-label">Name</span>
          <input v-model="form.name" type="text" class="aots-field w-full" maxlength="100" />
        </label>
        <label class="block">
          <span class="aots-label">Short name</span>
          <input v-model="form.short_name" type="text" class="aots-field w-full" maxlength="15" />
        </label>
        <label class="block">
          <span class="aots-label">Telescopes</span>
          <textarea v-model="form.telescopes" class="aots-field w-full" rows="2" />
        </label>
        <div class="grid grid-cols-3 gap-2">
          <label class="block">
            <span class="aots-label">Latitude (deg)</span>
            <input v-model="form.latitude" type="number" step="any" class="aots-field w-full" />
          </label>
          <label class="block">
            <span class="aots-label">Longitude (deg)</span>
            <input v-model="form.longitude" type="number" step="any" class="aots-field w-full" />
          </label>
          <label class="block">
            <span class="aots-label">Altitude (m)</span>
            <input v-model="form.altitude" type="number" step="any" class="aots-field w-full" />
          </label>
        </div>
        <label class="flex items-center gap-2">
          <input v-model="form.space_craft" type="checkbox" />
          Space craft
        </label>
        <label class="block">
          <span class="aots-label">Note</span>
          <textarea v-model="form.note" class="aots-field w-full" rows="2" />
        </label>
        <label class="block">
          <span class="aots-label">Website</span>
          <input v-model="form.url" type="text" class="aots-field w-full" maxlength="150" />
        </label>
        <label class="block">
          <span class="aots-label">Weather URL</span>
          <input v-model="form.weatherurl" type="text" class="aots-field w-full" maxlength="150" />
        </label>
        <AppAlert v-if="formError" kind="error">{{ formError }}</AppAlert>
      </div>
      <div class="flex gap-2 mt-4">
        <AppButton variant="primary" :disabled="saving" @click="saveObservatory">
          {{ saveLabel }}
        </AppButton>
        <AppButton variant="ghost" :disabled="saving" @click="closeDialog">
          Cancel
        </AppButton>
      </div>
    </div>
  </dialog>
</template>
