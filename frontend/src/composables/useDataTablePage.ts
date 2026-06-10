import { useQuery } from '@tanstack/vue-query'
import { computed, ref, watch, type Ref } from 'vue'
import { api, type PaginatedResponse } from '@/api/client'
import { useProjectStore } from '@/stores/project'

export interface ListColumn<T> {
  id: string
  header: string
  accessor?: (row: T) => unknown
}

export interface UseDataTableOptions {
  endpoint: string
  projectSlug: Ref<string>
  filters?: Ref<Record<string, string | number | boolean | string[] | undefined>>
  ordering?: Ref<string>
  enabled?: Ref<boolean>
}

export function useDataTablePage<T extends { pk: number }>(opts: UseDataTableOptions) {
  const projectStore = useProjectStore()
  const page = ref(1)
  const pageSize = ref(20)
  const selected = ref(new Set<number>())
  const ordering = opts.ordering ?? ref('')

  const queryKey = computed(() => [
    opts.endpoint,
    projectStore.currentProject?.pk,
    page.value,
    pageSize.value,
    ordering.value,
    opts.filters?.value,
  ])

  const query = useQuery({
    queryKey,
    queryFn: async () => {
      const project = projectStore.currentProject
      if (!project) return { count: 0, next: null, previous: null, results: [] as T[] }
      const params = new URLSearchParams({
        project: String(project.pk),
        page: String(page.value),
        page_size: String(pageSize.value),
      })
      if (ordering.value) params.set('ordering', ordering.value)
      if (opts.filters?.value) {
        for (const [k, v] of Object.entries(opts.filters.value)) {
          if (v === undefined || v === '' || v === false) continue
          if (Array.isArray(v)) {
            for (const item of v) {
              if (item !== undefined && item !== '') params.append(k, String(item))
            }
          } else {
            params.set(k, String(v))
          }
        }
      }
      return api<PaginatedResponse<T>>(`${opts.endpoint}?${params}`)
    },
    enabled: computed(() => (opts.enabled?.value ?? true) && !!projectStore.currentProject),
  })

  watch([page, pageSize, () => opts.filters?.value, ordering], () => {
    selected.value = new Set()
  })

  function toggleRow(pk: number) {
    const next = new Set(selected.value)
    if (next.has(pk)) next.delete(pk)
    else next.add(pk)
    selected.value = next
  }

  function toggleAll(rows: T[]) {
    if (selected.value.size === rows.length) selected.value = new Set()
    else selected.value = new Set(rows.map((r) => r.pk))
  }

  function clearSelection() {
    selected.value = new Set()
  }

  return { query, page, pageSize, ordering, selected, toggleRow, toggleAll, clearSelection }
}
