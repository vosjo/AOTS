import { ofetch } from 'ofetch'

export function setCsrfToken(token: string): void {
  window.__AOTS_BOOTSTRAP__ = {
    ...window.__AOTS_BOOTSTRAP__,
    csrfToken: token,
  }
}

export function getCsrfToken(): string {
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)
  if (match) {
    const fromCookie = decodeURIComponent(match[1])
    setCsrfToken(fromCookie)
    return fromCookie
  }
  return window.__AOTS_BOOTSTRAP__?.csrfToken ?? ''
}

export async function ensureCsrfToken(): Promise<void> {
  if (getCsrfToken()) return
  const data = await api<{ csrfToken: string }>('/api/auth/csrf/')
  setCsrfToken(data.csrfToken)
}

export const PERMISSION_DENIED_MESSAGE =
  'You do not have permission to perform this action.'

export function formatApiError(error: unknown): string {
  if (error && typeof error === 'object') {
    const err = error as { data?: unknown; message?: string; statusCode?: number; status?: number }
    const status = err.statusCode ?? err.status
    if (typeof err.data === 'string' && err.data.trim()) {
      return status === 403 ? err.data : err.data
    }
    if (err.data && typeof err.data === 'object' && err.data !== null) {
      const data = err.data as Record<string, unknown>
      if ('detail' in data) {
        const detail = data.detail
        if (typeof detail === 'string') return detail
        if (detail !== undefined) return JSON.stringify(detail, null, 2)
      }
      const fieldMessages = Object.entries(data)
        .map(([field, value]) => {
          if (Array.isArray(value)) {
            return `${field}: ${value.join(', ')}`
          }
          if (typeof value === 'string') {
            return `${field}: ${value}`
          }
          return `${field}: ${JSON.stringify(value)}`
        })
        .filter(Boolean)
      if (fieldMessages.length) return fieldMessages.join('\n')
    }
    if (status === 403) return PERMISSION_DENIED_MESSAGE
    if (err.message) return err.message
  }
  return String(error)
}

export const api = ofetch.create({
  baseURL: '/',
  credentials: 'include',
  onRequest({ options }) {
    const method = (options.method ?? 'GET').toUpperCase()
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const headers = new Headers(options.headers)
      headers.set('X-CSRFToken', getCsrfToken())
      options.headers = headers
    }
  },
})

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ProjectSummary {
  pk: number
  name: string
  slug: string
  is_public: boolean
  description?: string
  logo?: string | null
  can_add?: boolean
}

const DEFAULT_PROJECT_LOGO = '/static/images/default_logo.png'

export { DEFAULT_PROJECT_LOGO }

export function projectLogoUrl(project: Pick<ProjectSummary, 'logo'>): string {
  return project.logo || DEFAULT_PROJECT_LOGO
}

export interface MeResponse {
  authenticated: boolean
  id?: number
  username?: string
  email?: string
  is_superuser?: boolean
  api_key?: string | null
  has_api_secret?: boolean
  csrfToken?: string
}
