import { onUnmounted, reactive } from 'vue'
import { api } from '@/api/client'

export interface TaskPollStatus<T> {
  ready: boolean
  status: string
  error?: string
  result?: T & { error?: string }
  meta?: { current?: number; total?: number; star_name?: string }
}

export interface BulkTaskPollOptions<T> {
  label: string
  failureMessage: string
  onProgress?: (status: TaskPollStatus<T>, total: number) => string
}

export interface BulkTaskPollState<T> {
  status: string
  busy: boolean
  lastSummary: T | null
  dispose: () => void
}

export type StartBulkOptions = { all?: boolean }

export type StartBulkFn = (
  starIds: number[],
  projectId: number,
  options?: StartBulkOptions,
) => Promise<void>

export interface BulkFetchState<T> extends BulkTaskPollState<T> {
  startBulk: StartBulkFn
}

export function createBulkTaskPollState<T>() {
  let active = true

  const state = reactive({
    status: '',
    busy: false,
    lastSummary: null as T | null,
    dispose() {
      active = false
    },
  }) as BulkTaskPollState<T>

  async function pollTask(taskId: string, total: number, options: BulkTaskPollOptions<T>): Promise<T> {
    for (;;) {
      if (!active) throw new Error('Cancelled')
      const s = await api<TaskPollStatus<T>>(`/api/observations/tasks/${taskId}/`)
      if (!active) throw new Error('Cancelled')
      if (!s.ready) {
        state.status = options.onProgress?.(s, total) ?? `${options.label}… ${s.status}`
        await new Promise((r) => setTimeout(r, 2000))
        continue
      }
      if (s.status === 'SUCCESS') {
        if (s.result?.error) throw new Error(s.result.error)
        if (!s.result) throw new Error(`${options.label} finished without result`)
        return s.result
      }
      throw new Error(s.error || options.failureMessage)
    }
  }

  onUnmounted(() => {
    active = false
  })

  return { state, pollTask, isActive: () => active }
}

export function extendBulkFetchState<T>(
  state: BulkTaskPollState<T>,
  extensions: { startBulk: StartBulkFn },
): BulkFetchState<T> {
  return Object.assign(state, extensions)
}

export function progressWithMeta(label: string, total: number, meta?: TaskPollStatus<unknown>['meta']): string {
  const current = meta?.current
  const starName = meta?.star_name
  if (current != null) {
    return `${label}… ${current}/${meta?.total ?? total}${starName ? ` (${starName})` : ''}`
  }
  return `${label}…`
}
