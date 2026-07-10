import { onUnmounted, reactive } from 'vue'
import { api } from '@/api/client'

export interface AstraExportOptions {
  include_spectra?: boolean
  include_spectral_fits?: boolean
  include_photometry?: boolean
  include_lightcurves?: boolean
  include_sed_models?: boolean
  include_lc_fits?: boolean
  include_rv?: boolean
  creator_note?: string
  download_filename?: string
}

export function astraDownloadFilename(starName: string): string {
  const trimmed = starName.trim()
  const withoutSuffix = trimmed.toLowerCase().endsWith('.astra')
    ? trimmed.slice(0, -6)
    : trimmed
  const base = withoutSuffix
    .replace(/[^\w.\-+ ]+/g, '_')
    .replace(/\s+/g, '_')
    .replace(/^[._-]+|[._-]+$/g, '')
  return base ? `${base}.astra` : 'export.astra'
}

export function useAstraExport() {
  let active = true

  const state = reactive({
    status: '',
    busy: false,
    dispose() {
      active = false
    },
  })

  async function pollTask(taskId: string) {
    for (;;) {
      if (!active) return
      const s = await api<{ ready: boolean; status: string; error?: string; result?: { error?: string } }>(
        `/api/observations/tasks/${taskId}/`,
      )
      if (!active) return
      if (!s.ready) {
        state.status = `Building ASTRA package… ${s.status}`
        await new Promise((r) => setTimeout(r, 2000))
        continue
      }
      if (s.status === 'SUCCESS') {
        if (s.result?.error) throw new Error(s.result.error)
        window.location.href = `/api/interop/astra/export/${taskId}/file/`
        return
      }
      throw new Error(s.error || 'ASTRA export failed')
    }
  }

  async function exportStars(starIds: number[], projectId: number, options: AstraExportOptions = {}) {
    if (!starIds.length) return
    state.busy = true
    state.status = 'Starting export…'
    try {
      const res = await api<{ task_id: string }>('/api/interop/astra/export/', {
        method: 'POST',
        body: {
          project: projectId,
          star_ids: starIds,
          ...options,
        },
      })
      await pollTask(res.task_id)
      state.status = 'Download started.'
    } finally {
      state.busy = false
    }
  }

  onUnmounted(() => {
    active = false
  })

  return { state, exportStars }
}
