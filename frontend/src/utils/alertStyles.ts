export type AlertKind = 'info' | 'success' | 'warning' | 'error'

export function alertPanelClass(kind: AlertKind): string {
  switch (kind) {
    case 'success':
      return 'border-emerald-500/40 bg-emerald-950/40 text-emerald-100'
    case 'warning':
      return 'border-amber-500/40 bg-amber-950/40 text-amber-100'
    case 'error':
      return 'border-red-500/40 bg-red-950/40 text-red-100'
    default:
      return 'border-slate-500/40 bg-slate-800/60 text-slate-200'
  }
}

export function alertIconClass(kind: AlertKind): string {
  switch (kind) {
    case 'success':
      return 'text-emerald-400'
    case 'warning':
      return 'text-amber-400'
    case 'error':
      return 'text-red-400'
    default:
      return 'text-slate-400'
  }
}
