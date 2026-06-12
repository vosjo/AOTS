import { reactive } from 'vue'
import { api } from '@/api/client'

export type BulkKind = 'processed' | 'raw' | 'rawspecfiles' | 'lightcurves' | 'analyses'

export function useBulkDownload() {
  const state = reactive({
    status: '',
    busy: false,
    async start(kind: BulkKind, idList: number[], projectId: number) {
      if (!idList.length) return
      state.busy = true
      state.status = 'Preparing download…'
      try {
        const res = await api<{ task_id: string }>(
          `/api/observations/bulk-download/start/?kind=${encodeURIComponent(kind)}`,
          {
            method: 'POST',
            headers: {
              Projectid: String(projectId),
              Staridlist: idList.join(';'),
            },
          },
        )
        await pollTask(res.task_id)
      } finally {
        state.busy = false
        state.status = ''
      }
    },
  })

  async function pollTask(taskId: string) {
    for (;;) {
      const s = await api<{ ready: boolean; status: string; error?: string; result?: { error?: string } }>(
        `/api/observations/tasks/${taskId}/`,
      )
      if (!s.ready) {
        state.status = `Building ZIP… ${s.status}`
        await new Promise((r) => setTimeout(r, 2000))
        continue
      }
      if (s.status === 'SUCCESS') {
        if (s.result?.error) throw new Error(s.result.error)
        window.location.href = `/api/observations/bulk-download/${taskId}/file/`
        return
      }
      throw new Error(s.error || 'Bulk download failed')
    }
  }

  return state
}
