<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, ref, watch } from 'vue'
import { api, type PaginatedResponse } from '@/api/client'

interface UserChoice {
  id: number
  username: string
}

const props = defineProps<{
  modelValue: number[]
  label: string
}>()

const emit = defineEmits<{
  'update:modelValue': [number[]]
}>()

const search = ref('')
const debouncedSearch = ref('')

let debounceTimer: ReturnType<typeof setTimeout> | undefined
watch(search, (value) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    debouncedSearch.value = value
  }, 300)
})

const choicesQuery = useQuery({
  queryKey: computed(() => ['admin-user-choices', debouncedSearch.value]),
  queryFn: () => {
    const params = new URLSearchParams({ page_size: '100' })
    if (debouncedSearch.value) params.set('search', debouncedSearch.value)
    return api<PaginatedResponse<UserChoice>>(`/api/admin/users/choices/?${params}`)
  },
})

const selectedUsers = computed(() => new Set(props.modelValue))

function toggleUser(id: number) {
  const next = new Set(props.modelValue)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  emit('update:modelValue', [...next])
}

const choiceRows = computed(() => choicesQuery.data.value?.results ?? [])
</script>

<template>
  <div class="space-y-2">
    <label class="block text-sm font-medium text-slate-200">{{ label }}</label>
    <input v-model="search" class="aots-field" placeholder="Search users…" />
    <div class="max-h-40 overflow-y-auto rounded-md border border-slate-600 bg-slate-900 p-2">
      <label
        v-for="user in choiceRows"
        :key="user.id"
        class="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm hover:bg-slate-800"
      >
        <input
          type="checkbox"
          class="accent-sky-400"
          :checked="selectedUsers.has(user.id)"
          @change="toggleUser(user.id)"
        />
        <span>{{ user.username }}</span>
      </label>
      <p v-if="!choiceRows.length" class="px-2 py-1 text-sm text-slate-400">No users found.</p>
    </div>
    <p class="text-xs text-slate-400">{{ modelValue.length }} selected</p>
  </div>
</template>
