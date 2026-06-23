import { computed, type Ref } from 'vue'

interface QueryLike {
  isFetching: Ref<boolean>
  data: Ref<{ count?: number } | undefined>
}

function hasActiveFilterValues(
  values: Record<string, unknown>,
  search?: Ref<string>,
): boolean {
  if (search?.value.trim()) return true
  return Object.values(values).some((value) => {
    if (Array.isArray(value)) return value.length > 0
    if (typeof value === 'string') return value.trim() !== ''
    return Boolean(value)
  })
}

export function useEmptyTableMessage(opts: {
  query: QueryLike
  entity: string
  filters?: Ref<Record<string, unknown>>
  search?: Ref<string>
  scope?: 'project' | 'global'
}) {
  const emptyMessage = computed(() => {
    if (opts.query.isFetching.value || (opts.query.data.value?.count ?? 0) > 0) return ''
    if (hasActiveFilterValues(opts.filters?.value ?? {}, opts.search)) {
      return `No ${opts.entity} match the current filters.`
    }
    if (opts.scope === 'global') {
      return `No ${opts.entity} yet.`
    }
    return `No ${opts.entity} in this project yet.`
  })

  return { emptyMessage }
}
