import { createBulkTaskPollState, extendBulkFetchState, progressWithMeta } from '@/composables/useBulkTaskPoll'
import type { BulkFetchState } from '@/composables/useBulkTaskPoll'
import { api } from '@/api/client'

export interface VizierPhotometryBulkSummary {
  total: number
  ok: number
  no_match: number
  failed: number
  bands_updated_total: number
  errors: Array<{ star_pk: number; star_name?: string; message: string }>
}

export function useVizierPhotometryFetch(): BulkFetchState<VizierPhotometryBulkSummary> {
  const { state, pollTask } = createBulkTaskPollState<VizierPhotometryBulkSummary>()

  return extendBulkFetchState(state, {
    async startBulk(starIds: number[], projectId: number, options?: { all?: boolean }) {
      if (!options?.all && !starIds.length) return
      state.busy = true
      state.status = 'Starting VizieR photometry fetch…'
      state.lastSummary = null
      try {
        const res = await api<{ task_id: string; total: number }>(
          '/api/systems/stars/photometry/fetch-vizier-bulk/?async=1',
          {
            method: 'POST',
            headers: { Projectid: String(projectId) },
            body: options?.all ? { all: true } : { star_ids: starIds },
          },
        )
        state.lastSummary = await pollTask(res.task_id, res.total, {
          label: 'Fetching photometry from VizieR',
          failureMessage: 'VizieR photometry bulk fetch failed',
          onProgress: (s, total) => progressWithMeta('Fetching photometry from VizieR', total, s.meta),
        })
      } finally {
        state.busy = false
        state.status = ''
      }
    },
  })
}
