import { defineStore } from 'pinia'
import { ref } from 'vue'
import { applyTheme, getStoredTheme, type ThemeMode } from '@/theme'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(getStoredTheme())

  function setTheme(theme: ThemeMode) {
    mode.value = theme
    applyTheme(theme)
  }

  function toggle() {
    setTheme(mode.value === 'dark' ? 'light' : 'dark')
  }

  return { mode, setTheme, toggle }
})
