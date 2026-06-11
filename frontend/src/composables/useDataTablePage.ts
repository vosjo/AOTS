import { useQuery } from '@tanstack/vue-query'
import { computed, ref, watch, type Ref } from 'vue'
import { api, type PaginatedResponse } from '@/api/client'
import {
  useSpectraSectionSelection,
  type SpectraSectionKind,
} from '@/composables/useSpectraSectionSelection'
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
  spectraSectionSelection?: SpectraSectionKind
}

export function useDataTablePage<T extends { pk: number }>(opts: UseDataTableOptions) {
  const projectStore = useProjectStore()
  const page = ref(1)
  const pageSize = ref(20)
  const sectionSelection = opts.spectraSectionSelection ? useSpectraSectionSelection() : null
  const sectionKind = opts.spectraSectionSelection
  const localSelected = ref(new Set<number>())
  const selected = sectionSelection && sectionKind
    ? computed(() => sectionSelection.getSelectedSet(sectionKind))
    : localSelected
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
    if (!sectionSelection) localSelected.value = new Set()
  })

  watch(
    () => query.data.value?.results,
    (results) => {
      if (sectionSelection && sectionKind && results?.length) {
        sectionSelection.indexRows(sectionKind, results)
      }
    },
    { immediate: true },
  )

  function toggleRow(pkOrRow: number | T, rows?: T[]) {
    const pk = typeof pkOrRow === 'number' ? pkOrRow : pkOrRow.pk
    const row = typeof pkOrRow === 'number' ? rows?.find((entry) => entry.pk === pk) : pkOrRow
    if (sectionSelection && sectionKind) {
      sectionSelection.toggle(sectionKind, pk, row)
      return
    }
    const next = new Set(localSelected.value)
    if (next.has(pk)) next.delete(pk)
    else next.add(pk)
    localSelected.value = next
  }

  function toggleAll(rows: T[]) {
    if (sectionSelection && sectionKind) {
      sectionSelection.toggleAll(sectionKind, rows)
      return
    }
    if (localSelected.value.size === rows.length) localSelected.value = new Set()
    else localSelected.value = new Set(rows.map((r) => r.pk))
  }

  function clearSelection() {
    if (sectionSelection) sectionSelection.clearAll()
    else localSelected.value = new Set()
  }

  return { query, page, pageSize, ordering, selected, toggleRow, toggleAll, clearSelection }
}
