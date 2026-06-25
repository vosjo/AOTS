const DEFAULT_REDIRECT = '/w/projects/'

/** Accept only same-origin relative paths (no protocol-relative URLs). */
export function safeRedirectPath(raw: unknown): string {
  if (typeof raw !== 'string') return DEFAULT_REDIRECT
  const path = raw.trim()
  if (!path.startsWith('/') || path.startsWith('//')) return DEFAULT_REDIRECT
  return path
}
