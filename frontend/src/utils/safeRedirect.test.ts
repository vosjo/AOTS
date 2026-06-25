import { describe, expect, it } from 'vitest'
import { safeRedirectPath } from './safeRedirect'

describe('safeRedirectPath', () => {
  it('accepts relative paths', () => {
    expect(safeRedirectPath('/w/projects/')).toBe('/w/projects/')
  })

  it('rejects protocol-relative paths', () => {
    expect(safeRedirectPath('//evil.example/')).toBe('/w/projects/')
  })

  it('rejects non-string input', () => {
    expect(safeRedirectPath(undefined)).toBe('/w/projects/')
  })
})
