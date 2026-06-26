import { reactive } from 'vue'

export type ConfirmOptions = {
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  destructive?: boolean
}

export const confirmDialogState = reactive({
  open: false,
  title: 'Confirm',
  message: '',
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  destructive: true,
})

let pendingResolve: ((value: boolean) => void) | null = null

function applyOptions(options: ConfirmOptions) {
  const destructive = options.destructive !== false
  confirmDialogState.title = options.title ?? (destructive ? 'Delete?' : 'Confirm')
  confirmDialogState.message = options.message
  confirmDialogState.confirmLabel =
    options.confirmLabel ?? (destructive ? 'Delete' : 'Confirm')
  confirmDialogState.cancelLabel = options.cancelLabel ?? 'Cancel'
  confirmDialogState.destructive = destructive
}

export function confirmAction(options: ConfirmOptions | string): Promise<boolean> {
  const opts = typeof options === 'string' ? { message: options } : options

  if (confirmDialogState.open) {
    resolveConfirm(false)
  }

  applyOptions(opts)
  confirmDialogState.open = true

  return new Promise((resolve) => {
    pendingResolve = resolve
  })
}

export function resolveConfirm(value: boolean) {
  if (!confirmDialogState.open) return
  confirmDialogState.open = false
  const resolve = pendingResolve
  pendingResolve = null
  resolve?.(value)
}
