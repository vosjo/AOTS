<script setup lang="ts" generic="T extends { pk: number }">
import { computed, unref } from 'vue'
import AppButton from '@/components/AppButton.vue'
import type { ListColumn } from '@/composables/useDataTablePage'

const props = withDefaults(
  defineProps<{
    title?: string
    hideTitle?: boolean
    columns: ListColumn<T>[]
    rows: T[]
    count: number
    page: number
    pageSize: number
    loading?: boolean
    selected: Set<number>
    selectable?: boolean
  }>(),
  {
    selectable: true,
  },
)

// Avoid prop/computed name collision (`selectable` prop vs. template binding).
const showCheckboxes = computed(() => props.selectable)

const selectedSet = computed(() => {
  const value = unref(props.selected as Set<number>)
  return value instanceof Set ? value : new Set<number>()
})

const colSpan = computed(() => props.columns.length + (showCheckboxes.value ? 1 : 0))

const emit = defineEmits<{
  'update:page': [number]
  'update:pageSize': [number]
  'update:ordering': [string]
  toggleRow: [T]
  toggleAll: []
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)))

function isRowSelected(pk: number): boolean {
  return selectedSet.value.has(pk)
}

const headerChecked = computed(() => {
  if (!props.rows.length) return false
  return props.rows.every((row) => selectedSet.value.has(row.pk))
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 v-if="!hideTitle && title" class="text-2xl font-semibold text-aots-heading">{{ title }}</h1>
      <div v-else-if="!hideTitle" class="flex-1" />
      <div class="flex flex-wrap gap-2" :class="{ 'ml-auto': hideTitle }">
        <slot name="actions" />
      </div>
    </div>
    <slot name="filters" />
    <div class="aots-table-wrap">
      <table class="aots-table">
        <thead>
          <tr>
            <th v-if="showCheckboxes" class="w-10 px-2">
              <input
                type="checkbox"
                class="size-4 shrink-0 cursor-pointer rounded border border-aots bg-aots-surface-muted accent-aots ring-aots focus:ring-2 focus:outline-none"
                :checked="headerChecked"
                @change="emit('toggleAll')"
              />
            </th>
            <th v-for="col in columns" :key="col.id">{{ col.header }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="colSpan" class="p-4 text-center text-aots-muted">Loading…</td>
          </tr>
          <tr v-for="row in rows" :key="row.pk">
            <td v-if="showCheckboxes" class="w-10 px-2">
              <input
                type="checkbox"
                class="size-4 shrink-0 cursor-pointer rounded border border-aots bg-aots-surface-muted accent-aots ring-aots focus:ring-2 focus:outline-none"
                :checked="isRowSelected(row.pk)"
                @change="emit('toggleRow', row)"
              />
            </td>
            <td v-for="col in columns" :key="col.id">
              <slot :name="`cell-${col.id}`" :row="row">
                {{ col.accessor ? col.accessor(row) : (row as Record<string, unknown>)[col.id] }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="flex flex-wrap items-center gap-3 text-sm text-aots">
      <AppButton variant="secondary" :disabled="page <= 1" @click="emit('update:page', page - 1)">
        Prev
      </AppButton>
      <span>Page {{ page }} / {{ totalPages }} ({{ count }} rows)</span>
      <AppButton
        variant="secondary"
        :disabled="page >= totalPages"
        @click="emit('update:page', page + 1)"
      >
        Next
      </AppButton>
      <select
        class="aots-select w-auto"
        :value="pageSize"
        @change="emit('update:pageSize', Number(($event.target as HTMLSelectElement).value))"
      >
        <option :value="10">10 per page</option>
        <option :value="20">20 per page</option>
        <option :value="50">50 per page</option>
        <option :value="100">100 per page</option>
      </select>
    </div>
  </div>
</template>
