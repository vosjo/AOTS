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
    <label class="block text-sm font-medium text-aots">{{ label }}</label>
    <input v-model="search" class="aots-field" placeholder="Search users…" />
    <div class="max-h-40 overflow-y-auto rounded-md border border-aots bg-aots-page p-2">
      <label
        v-for="user in choiceRows"
        :key="user.id"
        class="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm hover:bg-aots-surface"
      >
        <input
          type="checkbox"
          class="accent-aots"
          :checked="selectedUsers.has(user.id)"
          @change="toggleUser(user.id)"
        />
        <span>{{ user.username }}</span>
      </label>
      <p v-if="!choiceRows.length" class="px-2 py-1 text-sm text-aots-muted">No users found.</p>
    </div>
    <p class="text-xs text-aots-muted">{{ modelValue.length }} selected</p>
  </div>
</template>
