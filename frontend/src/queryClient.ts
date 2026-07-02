import { QueryClient } from '@tanstack/vue-query'

/** Default cache freshness for API queries (lists, details, etc.). */
export const QUERY_STALE_TIME_MS = 60_000

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: QUERY_STALE_TIME_MS,
      // Still refetch on tab focus, but only when data is older than staleTime.
      refetchOnWindowFocus: true,
    },
  },
})
