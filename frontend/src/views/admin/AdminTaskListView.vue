<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import DataTablePage from '@/components/DataTablePage.vue'
import AppButton from '@/components/AppButton.vue'
import { api, type PaginatedResponse } from '@/api/client'

interface AdminTaskRow {
  pk: number
  task_id: string
  task_display: string
  task_name: string
  label: string
  username: string | null
  project_name: string | null
  status: string
  ready: boolean
  progress?: string
  created_at: string | null
  error?: string
  result?: unknown
  meta?: Record<string, unknown>
}

const search = ref('')
const activeOnly = ref(true)
const statusFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const expandedId = ref<string | null>(null)

const queryKey = computed(() => [
  '/api/admin/tasks/',
  page.value,
  pageSize.value,
  search.value,
  activeOnly.value,
  statusFilter.value,
])

const query = useQuery({
  queryKey,
  queryFn: async () => {
    const params = new URLSearchParams({
      page: String(page.value),
      page_size: String(pageSize.value),
    })
    if (search.value.trim()) params.set('search', search.value.trim())
    if (activeOnly.value) params.set('active_only', '1')
    if (statusFilter.value) params.set('status', statusFilter.value)
    return api<PaginatedResponse<AdminTaskRow>>(`/api/admin/tasks/?${params}`)
  },
  refetchInterval: ({ state }) => {
    const rows = state.data?.results ?? []
    const hasActive = rows.some((row) => !row.ready)
    return hasActive ? 3000 : false
  },
})

const rows = computed(() =>
  (query.data.value?.results ?? []).map((row, index) => ({
    ...row,
    pk: index + 1,
  })),
)

const hasActiveTasks = computed(() => rows.value.some((row) => !row.ready))

const columns = [
  { id: 'created_at', header: 'Started' },
  { id: 'task_display', header: 'Type' },
  { id: 'label', header: 'Label' },
  { id: 'username', header: 'User' },
  { id: 'project_name', header: 'Project' },
  { id: 'status', header: 'Status' },
  { id: 'progress', header: 'Progress' },
  { id: 'actions', header: '' },
]

const selected = ref(new Set<number>())
const timeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'medium',
})

function formatTime(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : timeFormatter.format(date)
}

function statusClass(status: string, ready: boolean): string {
  if (!ready && (status === 'PENDING' || status === 'STARTED' || status === 'PROGRESS')) {
    return 'text-amber-300'
  }
  if (status === 'SUCCESS') return 'text-emerald-400'
  if (status === 'FAILURE') return 'text-red-400'
  return 'text-aots-muted'
}

function toggleExpanded(taskId: string) {
  expandedId.value = expandedId.value === taskId ? null : taskId
}

function formatJson(value: unknown): string {
  if (value === undefined || value === null) return '—'
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-semibold text-aots-heading">Background tasks</h1>
      <p v-if="hasActiveTasks" class="text-sm text-aots-muted">
        Auto-refreshing every 3s while tasks are running
      </p>
    </div>

    <DataTablePage
      hide-title
      :columns="columns"
      :rows="rows"
      :count="query.data.value?.count ?? 0"
      :page="page"
      :page-size="pageSize"
      :loading="query.isFetching.value"
      empty-message="No background tasks recorded yet."
      :selected="selected"
      :selectable="false"
      @update:page="page = $event"
      @update:page-size="pageSize = $event"
    >
      <template #filters>
        <input
          v-model="search"
          class="aots-field min-w-[12rem] max-w-xs shrink-0"
          placeholder="Search tasks…"
        />
        <label class="inline-flex shrink-0 items-center gap-2 whitespace-nowrap text-sm text-aots">
          <input v-model="activeOnly" type="checkbox" class="rounded border-aots" />
          Active only
        </label>
        <select v-model="statusFilter" class="aots-field w-auto min-w-[10rem] shrink-0">
          <option value="">All statuses</option>
          <option value="PENDING">Pending</option>
          <option value="STARTED">Started</option>
          <option value="PROGRESS">In progress</option>
          <option value="SUCCESS">Success</option>
          <option value="FAILURE">Failure</option>
        </select>
        <AppButton variant="secondary" size="sm" class="shrink-0" @click="query.refetch()">
          Refresh
        </AppButton>
      </template>

      <template #cell-created_at="{ row }">
        <span class="whitespace-nowrap text-sm">{{ formatTime(row.created_at) }}</span>
      </template>

      <template #cell-label="{ row }">
        <span class="line-clamp-2 text-sm" :title="row.label">{{ row.label || '—' }}</span>
      </template>

      <template #cell-username="{ row }">
        <span class="text-sm">{{ row.username || '—' }}</span>
      </template>

      <template #cell-project_name="{ row }">
        <span class="text-sm">{{ row.project_name || '—' }}</span>
      </template>

      <template #cell-status="{ row }">
        <span class="text-sm font-medium" :class="statusClass(row.status, row.ready)">
          {{ row.status }}
        </span>
      </template>

      <template #cell-progress="{ row }">
        <span class="text-sm text-aots-muted">{{ row.progress || (row.ready ? 'Done' : '…') }}</span>
      </template>

      <template #cell-actions="{ row }">
        <AppButton variant="link" size="sm" @click="toggleExpanded(row.task_id)">
          {{ expandedId === row.task_id ? 'Hide' : 'Details' }}
        </AppButton>
      </template>
    </DataTablePage>

    <section
      v-if="expandedId && rows.find((row) => row.task_id === expandedId)"
      class="aots-panel space-y-3"
    >
      <template v-for="row in rows.filter((r) => r.task_id === expandedId)" :key="row.task_id">
        <h2 class="font-medium text-aots-heading">Task details</h2>
        <dl class="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt class="text-aots-muted">Task ID</dt>
            <dd class="break-all font-mono text-xs">{{ row.task_id }}</dd>
          </div>
          <div>
            <dt class="text-aots-muted">Celery name</dt>
            <dd class="break-all font-mono text-xs">{{ row.task_name || '—' }}</dd>
          </div>
        </dl>
        <div v-if="row.error">
          <p class="text-sm font-medium text-red-400">Error</p>
          <pre class="mt-1 overflow-x-auto rounded bg-aots-surface p-3 text-xs">{{ row.error }}</pre>
        </div>
        <div v-if="row.result !== undefined">
          <p class="text-sm font-medium text-aots-heading">Result</p>
          <pre class="mt-1 max-h-64 overflow-auto rounded bg-aots-surface p-3 text-xs">{{ formatJson(row.result) }}</pre>
        </div>
        <div v-else-if="row.meta">
          <p class="text-sm font-medium text-aots-heading">Progress meta</p>
          <pre class="mt-1 overflow-x-auto rounded bg-aots-surface p-3 text-xs">{{ formatJson(row.meta) }}</pre>
        </div>
      </template>
    </section>
  </div>
</template>
