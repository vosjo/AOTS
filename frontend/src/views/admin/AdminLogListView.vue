<script setup lang="ts">
import { computed, ref } from 'vue'
import DataTablePage from '@/components/DataTablePage.vue'
import { useAdminList } from '@/composables/useAdminList'
import { useEmptyTableMessage } from '@/composables/useEmptyTableMessage'

interface AdminLogRow {
  id: number
  pk: number
  action_time: string
  username: string | null
  object_repr: string
  action_flag_label: string
  change_message: string
  change_message_display: string
}

const search = ref('')
const { query, page, pageSize } = useAdminList<AdminLogRow>({
  endpoint: '/api/admin/log-entries/',
  search,
})

const rows = computed(() =>
  (query.data.value?.results ?? []).map((row) => ({ ...row, pk: row.id })),
)
const { emptyMessage } = useEmptyTableMessage({
  query,
  search,
  entity: 'log entries',
  scope: 'global',
})

const columns = [
  { id: 'action_time', header: 'Time' },
  { id: 'username', header: 'User' },
  { id: 'object_repr', header: 'Object' },
  { id: 'action_flag_label', header: 'Action' },
  { id: 'change_message_display', header: 'Message' },
]

const selected = ref(new Set<number>())
const timeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'medium',
})

function formatActionTime(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : timeFormatter.format(date)
}
</script>

<template>
  <DataTablePage
    title="Admin log"
    :columns="columns"
    :rows="rows"
    :count="query.data.value?.count ?? 0"
    :page="page"
    :page-size="pageSize"
    :loading="query.isFetching.value"
    :empty-message="emptyMessage"
    :selected="selected"
    :selectable="false"
    @update:page="page = $event"
    @update:page-size="pageSize = $event"
  >
    <template #filters>
      <input v-model="search" class="aots-field max-w-xs" placeholder="Search log entries…" />
    </template>
    <template #cell-action_time="{ row }">
      <span class="whitespace-nowrap text-sm">{{ formatActionTime(row.action_time) }}</span>
    </template>
    <template #cell-object_repr="{ row }">
      <span class="line-clamp-2 text-sm" :title="row.object_repr">{{ row.object_repr }}</span>
    </template>
    <template #cell-action_flag_label="{ row }">
      <span class="text-sm">{{ row.action_flag_label }}</span>
    </template>
    <template #cell-change_message_display="{ row }">
      <span
        class="line-clamp-3 text-sm text-aots"
        :title="row.change_message_display || row.change_message"
      >
        {{ row.change_message_display || '—' }}
      </span>
    </template>
  </DataTablePage>
</template>
