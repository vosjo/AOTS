<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { CheckCircle2, Pencil, Plus, Trash2, XCircle } from 'lucide-vue-next'
import DataTablePage from '@/components/DataTablePage.vue'
import { useDataTablePage } from '@/composables/useDataTablePage'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

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
const projectStore = useProjectStore()

const { query, page, pageSize, selected, toggleRow, toggleAll } = useDataTablePage<ObservatoryRow>({
  endpoint: '/api/observations/observatories/',
  projectSlug,
})
const rows = computed(() => query.data.value?.results ?? [])

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
  if (auth.isAuthenticated) cols.push({ id: 'actions', header: 'Action' })
  return cols
})

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
    await query.refetch()
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'Save failed'
  } finally {
    saving.value = false
  }
}

async function deleteObservatory(row: ObservatoryRow) {
  if (!confirm('Are you sure you want to delete this Observatory? This cannot be undone')) return
  try {
    await api(`/api/observations/observatories/${row.pk}/`, { method: 'DELETE' })
    await query.refetch()
  } catch (e) {
    const status = (e as { statusCode?: number })?.statusCode
    if (status === 500) {
      alert('Observatory can not be deleted, since spectra still refer to it.')
    }
  }
}
</script>

<template>
  <DataTablePage
    title="Observatories"
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
        Add observatory
      </button>
    </template>

    <template #cell-name="{ row }">
      <a
        v-if="row.url"
        :href="observatoryHref(row.url)"
        target="_blank"
        rel="noopener"
        class="text-sky-400 hover:text-sky-300"
      >
        {{ row.name }}
      </a>
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
      <span class="text-slate-300 line-clamp-2">{{ row.note || '—' }}</span>
    </template>

    <template v-if="auth.isAuthenticated" #cell-actions="{ row }">
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="p-1 text-slate-300 hover:text-sky-400"
          title="Edit observatory"
          @click="openEdit(row)"
        >
          <Pencil class="w-4 h-4" />
        </button>
        <button
          type="button"
          class="p-1 text-slate-300 hover:text-red-400"
          title="Delete observatory"
          @click="deleteObservatory(row)"
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
        <p v-if="formError" class="text-sm text-red-400">{{ formError }}</p>
      </div>
      <div class="flex gap-2 mt-4">
        <button type="button" class="aots-btn-primary" :disabled="saving" @click="saveObservatory">
          {{ saveLabel }}
        </button>
        <button type="button" class="aots-btn-ghost" :disabled="saving" @click="closeDialog">
          Cancel
        </button>
      </div>
    </div>
  </dialog>
</template>
