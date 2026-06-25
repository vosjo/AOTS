import { createBulkTaskPollState, extendBulkFetchState, progressWithMeta } from '@/composables/useBulkTaskPoll'
import type { BulkFetchState } from '@/composables/useBulkTaskPoll'
import { api } from '@/api/client'

export interface TessBulkSummary {
  total: number
  ok: number
  no_match: number
  partial: number
  failed: number
  imported_lightcurves: number
  skipped_duplicates: number
  errors: Array<{ star_pk: number; star_name?: string; message: string }>
}

export function useTessFetch(): BulkFetchState<TessBulkSummary> {
  const { state, pollTask } = createBulkTaskPollState<TessBulkSummary>()

  return extendBulkFetchState(state, {
    async startBulk(starIds: number[], projectId: number, options?: { all?: boolean }) {
      if (!options?.all && !starIds.length) return
      state.busy = true
      state.status = 'Starting TESS fetch…'
      state.lastSummary = null
      try {
        const res = await api<{ task_id: string; total: number }>(
          '/api/systems/stars/tess/fetch-bulk/?async=1',
          {
            method: 'POST',
            headers: { Projectid: String(projectId) },
            body: options?.all ? { all: true } : { star_ids: starIds },
          },
        )
        state.lastSummary = await pollTask(res.task_id, res.total, {
          label: 'Fetching TESS',
          failureMessage: 'TESS bulk fetch failed',
          onProgress: (s, total) => progressWithMeta('Fetching TESS', total, s.meta),
        })
      } finally {
        state.busy = false
        state.status = ''
      }
    },
  })
}
