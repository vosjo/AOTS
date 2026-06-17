export type ThemeMode = 'dark' | 'light'

export const THEME_STORAGE_KEY = 'aots-theme'

export function getStoredTheme(): ThemeMode {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    /* private browsing */
  }
  return 'dark'
}

export function applyTheme(theme: ThemeMode): void {
  document.documentElement.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    /* private browsing */
  }
}

export function initTheme(): ThemeMode {
  const theme = getStoredTheme()
  applyTheme(theme)
  return theme
}
