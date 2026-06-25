import { createBulkTaskPollState, progressWithMeta } from '@/composables/useBulkTaskPoll'
import { api } from '@/api/client'

export interface GaiaBulkSummary {
  total: number
  ok: number
  no_match: number
  partial: number
  failed: number
  errors: Array<{ star_pk: number; star_name?: string; message: string }>
}

export function useGaiaFetch() {
  const { state, pollTask } = createBulkTaskPollState<GaiaBulkSummary>()

  Object.assign(state, {
    async startBulk(starIds: number[], projectId: number, options?: { all?: boolean }) {
      if (!options?.all && !starIds.length) return
      state.busy = true
      state.status = 'Starting Gaia DR3 fetch…'
      state.lastSummary = null
      try {
        const res = await api<{ task_id: string; total: number }>(
          '/api/systems/stars/gaia/fetch-bulk/?async=1',
          {
            method: 'POST',
            headers: { Projectid: String(projectId) },
            body: options?.all ? { all: true } : { star_ids: starIds },
          },
        )
        state.lastSummary = await pollTask(res.task_id, res.total, {
          label: 'Fetching Gaia DR3',
          failureMessage: 'Gaia DR3 bulk fetch failed',
          onProgress: (s, total) => progressWithMeta('Fetching Gaia DR3', total, s.meta),
        })
      } finally {
        state.busy = false
        state.status = ''
      }
    },
  })

  return state
}
