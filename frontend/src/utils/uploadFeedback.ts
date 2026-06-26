import { alertIconClass, alertPanelClass, type AlertKind } from '@/utils/alertStyles'

export type UploadFeedbackKind = AlertKind

export interface UploadFeedbackItem {
  kind: UploadFeedbackKind
  title: string
  detail?: string
  filename?: string
}

function normalizeMessage(message: string): string {
  return message.replace(/^["']|["']$/g, '').trim()
}

function basename(path: string) {
  const parts = path.split('/')
  return parts[parts.length - 1] || path
}

function splitFilenameAndDetail(message: string): { filename?: string; detail: string } {
  const colonIdx = message.indexOf(': ')
  if (colonIdx > 0 && colonIdx < 120) {
    const head = message.slice(0, colonIdx).trim()
    const tail = message.slice(colonIdx + 2).trim()
    if (head.includes('.fits') || head.includes('.txt') || head.includes('.fit')) {
      return { filename: basename(head), detail: tail }
    }
  }
  return { detail: message }
}

function classifyFormatError(message: string, lower: string): UploadFeedbackItem | null {
  const keyMatch = message.match(/key ['"]([^'"]+)['"] does not exist/i)
  if (keyMatch) {
    const field = keyMatch[1]
    return {
      kind: 'error',
      title: 'Invalid spectrum file',
      detail:
        field.toLowerCase() === 'wavelength'
          ? 'This file has no recognizable wavelength column. AOTS expects a 1D spectrum (wavelength + flux), not a generic FITS table or image.'
          : `Required data column or header field "${field}" is missing from this file.`,
    }
  }

  if (lower.includes('unsupported spectrum format') || lower.includes('no wavelength column')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'error',
      title: 'Invalid spectrum file',
      filename,
      detail,
    }
  }

  if (lower.includes('incomplete fits header') || lower.includes('keyword') && lower.includes('not found')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'error',
      title: 'Incomplete FITS header',
      filename,
      detail:
        detail ||
        'Required header information is missing. Enable "Add to / modify header data" and fill in the values manually.',
    }
  }

  if (lower.includes('could not be read as text') || lower.includes('unicodedecodeerror')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'error',
      title: 'Unreadable file',
      filename,
      detail: detail || 'Upload a valid FITS or plain-text spectrum file.',
    }
  }

  return null
}

function classifyLightCurveMessage(message: string, lower: string): UploadFeedbackItem | null {
  if (lower.includes('light curve is a duplicate')) {
    return {
      kind: 'warning',
      title: 'Duplicate light curve',
      detail: message,
    }
  }

  if (lower.includes('new light curve') && lower.includes('added to')) {
    return {
      kind: 'success',
      title: 'Light curve imported',
      detail: message,
    }
  }

  if (lower.includes('unsupported light curve format') || lower.includes('no time column found')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'error',
      title: 'Invalid light curve file',
      filename,
      detail: detail || message,
    }
  }

  if (lower.includes('empty or invalid fits')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'error',
      title: 'Invalid FITS file',
      filename,
      detail: detail || message,
    }
  }

  if (lower.includes('could not be stored')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'error',
      title: 'Upload failed',
      filename,
      detail: detail || message,
    }
  }

  return null
}

function classifyUploadMessage(rawMessage: string): UploadFeedbackItem {
  const message = normalizeMessage(rawMessage)
  const lower = message.toLowerCase()

  const lightCurveMessage = classifyLightCurveMessage(message, lower)
  if (lightCurveMessage) return lightCurveMessage

  const duplicateMatch = message.match(/Specfile\s+(\S+)\s+is a duplicate/i)
  if (duplicateMatch) {
    const filename = basename(duplicateMatch[1])
    return {
      kind: 'warning',
      title: 'Duplicate spectrum',
      filename,
      detail: 'This file is already in the database and was not imported again.',
    }
  }

  if (lower.includes('duplicate')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'warning',
      title: 'Duplicate file',
      filename,
      detail: detail || message,
    }
  }

  const formatError = classifyFormatError(message, lower)
  if (formatError) return formatError

  if (
    lower.includes('no star found')
    || lower.includes('not added to database')
    || lower.includes('exception occurred')
    || lower.includes('upload failed')
  ) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'error',
      title: 'Upload failed',
      filename,
      detail: detail || message,
    }
  }

  if (lower.includes('added to')) {
    const { filename, detail } = splitFilenameAndDetail(message)
    return {
      kind: 'success',
      title: 'File imported',
      filename,
      detail: detail || message,
    }
  }

  if (lower.includes('provided information not added')) {
    return {
      kind: 'warning',
      title: 'Header note not saved',
      detail: message,
    }
  }

  // Unknown processing errors should be shown as errors, not neutral info.
  const { filename, detail } = splitFilenameAndDetail(message)
  return {
    kind: 'error',
    title: 'Upload failed',
    filename,
    detail: detail || message,
  }
}

export function extractUploadDetail(res: unknown): string {
  if (typeof res === 'string') return res
  if (res && typeof res === 'object' && 'detail' in res) {
    const detail = (res as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return ''
}

export function parseUploadFeedback(raw: string): UploadFeedbackItem[] {
  return raw
    .split(';')
    .map((part) => part.trim())
    .filter(Boolean)
    .map(classifyUploadMessage)
}

export function uploadFeedbackPanelClass(kind: UploadFeedbackKind): string {
  return alertPanelClass(kind)
}

export function uploadFeedbackIconClass(kind: UploadFeedbackKind): string {
  return alertIconClass(kind)
}
