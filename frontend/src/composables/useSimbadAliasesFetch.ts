import { createBulkTaskPollState, progressWithMeta } from '@/composables/useBulkTaskPoll'
import { api } from '@/api/client'

export interface SimbadAliasesBulkSummary {
  total: number
  ok: number
  no_match: number
  partial: number
  failed: number
  added_total: number
  errors: Array<{ star_pk: number; star_name?: string; message: string }>
}

export function useSimbadAliasesFetch() {
  const { state, pollTask } = createBulkTaskPollState<SimbadAliasesBulkSummary>()

  Object.assign(state, {
    async startBulk(starIds: number[], projectId: number, options?: { all?: boolean }) {
      if (!options?.all && !starIds.length) return
      state.busy = true
      state.status = 'Starting Simbad alias sync…'
      state.lastSummary = null
      try {
        const res = await api<{ task_id: string; total: number }>(
          '/api/systems/stars/simbad/fetch-bulk/?async=1',
          {
            method: 'POST',
            headers: { Projectid: String(projectId) },
            body: options?.all ? { all: true } : { star_ids: starIds },
          },
        )
        state.lastSummary = await pollTask(res.task_id, res.total, {
          label: 'Updating Simbad aliases',
          failureMessage: 'Simbad alias bulk sync failed',
          onProgress: (s, total) => progressWithMeta('Updating Simbad aliases', total, s.meta),
        })
      } finally {
        state.busy = false
        state.status = ''
      }
    },
  })

  return state
}
