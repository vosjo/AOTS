import { reactive } from 'vue'
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
  const state = reactive({
    status: '',
    busy: false,
    lastSummary: null as GaiaBulkSummary | null,
    async startBulk(starIds: number[], projectId: number) {
      if (!starIds.length) return
      state.busy = true
      state.status = 'Starting Gaia DR3 fetch…'
      state.lastSummary = null
      try {
        const res = await api<{ task_id: string; total: number }>(
          '/api/systems/stars/gaia/fetch-bulk/?async=1',
          {
            method: 'POST',
            headers: {
              Projectid: String(projectId),
            },
            body: { star_ids: starIds },
          },
        )
        state.lastSummary = await pollTask(res.task_id, res.total)
      } finally {
        state.busy = false
        state.status = ''
      }
    },
  })

  async function pollTask(taskId: string, total: number): Promise<GaiaBulkSummary> {
    for (;;) {
      const s = await api<{
        ready: boolean
        status: string
        error?: string
        result?: GaiaBulkSummary & { error?: string }
        meta?: { current?: number; total?: number; star_name?: string }
      }>(`/api/observations/tasks/${taskId}/`)

      if (!s.ready) {
        const current = s.meta?.current
        const starName = s.meta?.star_name
        if (current != null) {
          state.status = `Fetching Gaia DR3… ${current}/${s.meta?.total ?? total}${
            starName ? ` (${starName})` : ''
          }`
        } else {
          state.status = `Fetching Gaia DR3… ${s.status}`
        }
        await new Promise((r) => setTimeout(r, 2000))
        continue
      }
      if (s.status === 'SUCCESS') {
        if (s.result?.error) throw new Error(s.result.error)
        if (!s.result) throw new Error('Gaia fetch finished without result')
        return s.result
      }
      throw new Error(s.error || 'Gaia DR3 bulk fetch failed')
    }
  }

  return state
}
