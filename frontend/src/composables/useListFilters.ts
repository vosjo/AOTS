import { ref, type Ref } from 'vue'
import { carryOverFilter } from '@/composables/useCarryOver'

export function useListFilters<T extends Record<string, string>>(
  defaultFields: T,
  options?: { carryOver?: boolean },
) {
  const fieldKeys = Object.keys(defaultFields)
  const filters = ref({
    ...defaultFields,
    ...(options?.carryOver ? carryOverFilter() : {}),
  }) as Ref<Record<string, string>>

  function clearFilters() {
    const next: Record<string, string> = {}
    for (const key of fieldKeys) next[key] = ''
    filters.value = next
  }

  return { filters, clearFilters }
}
