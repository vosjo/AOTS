export type AlertKind = 'info' | 'success' | 'warning' | 'error'

export function alertPanelClass(kind: AlertKind): string {
  switch (kind) {
    case 'success':
      return 'aots-alert aots-alert-success'
    case 'warning':
      return 'aots-alert aots-alert-warning'
    case 'error':
      return 'aots-alert aots-alert-error'
    default:
      return 'aots-alert aots-alert-info'
  }
}

export function alertIconClass(kind: AlertKind): string {
  switch (kind) {
    case 'success':
      return 'aots-alert-success-icon'
    case 'warning':
      return 'aots-alert-warning-icon'
    case 'error':
      return 'aots-alert-error-icon'
    default:
      return 'aots-alert-info-icon'
  }
}
