import { useQuery } from '@tanstack/vue-query'
import { computed, ref, watch, type Ref } from 'vue'
import { api, type PaginatedResponse } from '@/api/client'

export interface AdminListOptions {
  endpoint: string
  filters?: Ref<Record<string, string | number | boolean | undefined>>
  search?: Ref<string>
  ordering?: Ref<string>
}

export function useAdminList<T>(opts: AdminListOptions) {
  const page = ref(1)
  const pageSize = ref(20)
  const ordering = opts.ordering ?? ref('')

  const queryKey = computed(() => [
    opts.endpoint,
    page.value,
    pageSize.value,
    ordering.value,
    opts.filters?.value,
    opts.search?.value,
  ])

  const query = useQuery({
    queryKey,
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page.value),
        page_size: String(pageSize.value),
      })
      if (ordering.value) params.set('ordering', ordering.value)
      if (opts.search?.value) params.set('search', opts.search.value)
      if (opts.filters?.value) {
        for (const [key, value] of Object.entries(opts.filters.value)) {
          if (value === undefined || value === '') continue
          params.set(key, String(value))
        }
      }
      return api<PaginatedResponse<T>>(`${opts.endpoint}?${params}`)
    },
  })

  watch([page, pageSize, () => opts.filters?.value, () => opts.search?.value, ordering], () => {
    page.value = Math.max(1, page.value)
  })

  return { query, page, pageSize, ordering }
}

export function rowPk(row: { pk?: number; id?: number }): number {
  return row.pk ?? row.id ?? 0
}
