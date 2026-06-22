import { ofetch } from 'ofetch'

export function getCsrfToken(): string {
  const fromBootstrap = window.__AOTS_BOOTSTRAP__?.csrfToken
  if (fromBootstrap) return fromBootstrap
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export async function ensureCsrfToken(): Promise<void> {
  if (getCsrfToken()) return
  const data = await api<{ csrfToken: string }>('/api/auth/csrf/')
  window.__AOTS_BOOTSTRAP__ = {
    ...window.__AOTS_BOOTSTRAP__,
    csrfToken: data.csrfToken,
  }
}

export function formatApiError(error: unknown): string {
  if (error && typeof error === 'object') {
    const err = error as { data?: unknown; message?: string }
    if (typeof err.data === 'string' && err.data.trim()) return err.data
    if (err.data && typeof err.data === 'object' && err.data !== null && 'detail' in err.data) {
      const detail = (err.data as { detail: unknown }).detail
      if (typeof detail === 'string') return detail
      if (detail !== undefined) return JSON.stringify(detail, null, 2)
    }
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
  preview_starmap?: string | null
}

const DEFAULT_PROJECT_LOGO = '/static/images/default_logo.png'

export { DEFAULT_PROJECT_LOGO }

export function projectLogoUrl(project: Pick<ProjectSummary, 'logo' | 'preview_starmap'>): string {
  return project.logo || project.preview_starmap || DEFAULT_PROJECT_LOGO
}

export interface MeResponse {
  authenticated: boolean
  id?: number
  username?: string
  email?: string
  is_superuser?: boolean
  api_key?: string | null
  has_api_secret?: boolean
}
