import { reactive } from 'vue'
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
  const state = reactive({
    status: '',
    busy: false,
    lastSummary: null as SimbadAliasesBulkSummary | null,
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
            headers: {
              Projectid: String(projectId),
            },
            body: options?.all ? { all: true } : { star_ids: starIds },
          },
        )
        state.lastSummary = await pollTask(res.task_id, res.total)
      } finally {
        state.busy = false
        state.status = ''
      }
    },
  })

  async function pollTask(taskId: string, total: number): Promise<SimbadAliasesBulkSummary> {
    for (;;) {
      const s = await api<{
        ready: boolean
        status: string
        error?: string
        result?: SimbadAliasesBulkSummary & { error?: string }
        meta?: { current?: number; total?: number; star_name?: string }
      }>(`/api/observations/tasks/${taskId}/`)

      if (!s.ready) {
        const current = s.meta?.current
        const starName = s.meta?.star_name
        if (current != null) {
          state.status = `Updating Simbad aliases… ${current}/${s.meta?.total ?? total}${
            starName ? ` (${starName})` : ''
          }`
        } else {
          state.status = `Updating Simbad aliases… ${s.status}`
        }
        await new Promise((r) => setTimeout(r, 2000))
        continue
      }
      if (s.status === 'SUCCESS') {
        if (s.result?.error) throw new Error(s.result.error)
        if (!s.result) throw new Error('Simbad alias sync finished without result')
        return s.result
      }
      throw new Error(s.error || 'Simbad alias bulk sync failed')
    }
  }

  return state
}
