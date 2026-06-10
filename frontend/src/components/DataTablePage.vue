<script setup lang="ts" generic="T extends { pk: number }">
import { computed } from 'vue'
import type { ListColumn } from '@/composables/useDataTablePage'

const props = defineProps<{
  title: string
  columns: ListColumn<T>[]
  rows: T[]
  count: number
  page: number
  pageSize: number
  loading?: boolean
  selected: Set<number>
}>()

const emit = defineEmits<{
  'update:page': [number]
  'update:pageSize': [number]
  'update:ordering': [string]
  toggleRow: [number]
  toggleAll: []
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)))
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-semibold text-slate-50">{{ title }}</h1>
      <div class="flex flex-wrap gap-2">
        <slot name="actions" />
      </div>
    </div>
    <slot name="filters" />
    <div class="aots-table-wrap">
      <table class="aots-table">
        <thead>
          <tr>
            <th class="w-8"><input type="checkbox" class="accent-sky-400" @change="emit('toggleAll')" /></th>
            <th v-for="col in columns" :key="col.id">{{ col.header }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="p-4 text-center text-slate-300">Loading…</td>
          </tr>
          <tr v-for="row in rows" :key="row.pk">
            <td>
              <input
                type="checkbox"
                class="accent-sky-400"
                :checked="selected.has(row.pk)"
                @change="emit('toggleRow', row.pk)"
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
    <div class="flex flex-wrap items-center gap-3 text-sm text-slate-200">
      <button
        class="aots-btn-secondary"
        :disabled="page <= 1"
        @click="emit('update:page', page - 1)"
      >
        Prev
      </button>
      <span>Page {{ page }} / {{ totalPages }} ({{ count }} rows)</span>
      <button
        class="aots-btn-secondary"
        :disabled="page >= totalPages"
        @click="emit('update:page', page + 1)"
      >
        Next
      </button>
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
