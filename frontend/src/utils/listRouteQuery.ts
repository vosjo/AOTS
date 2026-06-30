/** Defaults for list views synced to the route query string. */
export const LIST_ROUTE_DEFAULT_PAGE = 1
export const LIST_ROUTE_DEFAULT_PAGE_SIZE = 20

export type ListRouteFilterValue = string | number | boolean | string[] | undefined

export function normalizeRouteQuery(
  query: Record<string, unknown>,
): Record<string, string | string[] | undefined> {
  const normalized: Record<string, string | string[] | undefined> = {}
  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined) continue
    if (Array.isArray(value)) {
      normalized[key] = value.filter((item): item is string => typeof item === 'string')
      continue
    }
    if (typeof value === 'string') normalized[key] = value
  }
  return normalized
}

export function parseRouteFilterValue(
  raw: string | string[] | undefined,
  isArray: boolean,
): string | string[] {
  if (raw === undefined) return isArray ? [] : ''
  if (Array.isArray(raw)) return isArray ? raw : (raw[0] ?? '')
  if (isArray) {
    return raw
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean)
  }
  return raw
}

export function readListStateFromQuery(
  query: Record<string, string | string[] | undefined>,
  filters: Record<string, ListRouteFilterValue> | undefined,
): { page: number; pageSize: number; ordering: string; filters?: Record<string, ListRouteFilterValue> } {
  const pageRaw = query.page
  const page = Math.max(
    LIST_ROUTE_DEFAULT_PAGE,
    parseInt(Array.isArray(pageRaw) ? pageRaw[0] : (pageRaw ?? ''), 10) || LIST_ROUTE_DEFAULT_PAGE,
  )

  const pageSizeRaw = query.page_size
  const pageSize = Math.max(
    1,
    parseInt(
      Array.isArray(pageSizeRaw) ? pageSizeRaw[0] : (pageSizeRaw ?? ''),
      10,
    ) || LIST_ROUTE_DEFAULT_PAGE_SIZE,
  )

  const orderingRaw = query.ordering
  const ordering = Array.isArray(orderingRaw) ? (orderingRaw[0] ?? '') : (orderingRaw ?? '')

  if (!filters) {
    return { page, pageSize, ordering }
  }

  const nextFilters: Record<string, ListRouteFilterValue> = { ...filters }
  for (const key of Object.keys(nextFilters)) {
    const isArray = Array.isArray(nextFilters[key])
    nextFilters[key] = parseRouteFilterValue(query[key], isArray)
  }

  return { page, pageSize, ordering, filters: nextFilters }
}

export function buildListRouteQuery(options: {
  page: number
  pageSize: number
  ordering?: string
  filters?: Record<string, ListRouteFilterValue>
}): Record<string, string> {
  const query: Record<string, string> = {}

  if (options.page > LIST_ROUTE_DEFAULT_PAGE) {
    query.page = String(options.page)
  }
  if (options.pageSize !== LIST_ROUTE_DEFAULT_PAGE_SIZE) {
    query.page_size = String(options.pageSize)
  }
  if (options.ordering) {
    query.ordering = options.ordering
  }
  if (options.filters) {
    for (const [key, value] of Object.entries(options.filters)) {
      if (value === undefined || value === '' || value === false) continue
      if (Array.isArray(value)) {
        if (value.length) query[key] = value.join(',')
      } else {
        query[key] = String(value)
      }
    }
  }

  return query
}

export function managedListRouteKeys(
  filterKeys: string[],
  includeOrdering: boolean,
): string[] {
  const keys = ['page', 'page_size', ...filterKeys]
  if (includeOrdering) keys.push('ordering')
  return keys
}

export function mergeListRouteQuery(
  current: Record<string, string | string[] | undefined>,
  listQuery: Record<string, string>,
  managedKeys: string[],
): Record<string, string> {
  const next: Record<string, string> = {}
  for (const [key, value] of Object.entries(current)) {
    if (managedKeys.includes(key)) continue
    if (Array.isArray(value)) next[key] = value.join(',')
    else if (value !== undefined) next[key] = value
  }
  return { ...next, ...listQuery }
}
