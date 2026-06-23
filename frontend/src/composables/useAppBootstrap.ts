import { computed, ref } from 'vue'
import { api, setCsrfToken } from '@/api/client'

const testInstallationRef = ref(
  window.__AOTS_BOOTSTRAP__?.testInstallation === true,
)

export async function initAppBootstrap(): Promise<void> {
  try {
    const data = await api<{ csrfToken: string; testInstallation?: boolean }>('/api/bootstrap/')
    window.__AOTS_BOOTSTRAP__ = {
      ...window.__AOTS_BOOTSTRAP__,
      csrfToken: data.csrfToken,
      testInstallation: data.testInstallation === true,
    }
    setCsrfToken(data.csrfToken)
    testInstallationRef.value = data.testInstallation === true
  } catch {
    // Fall back to inline bootstrap from the Django SPA shell.
  }
}

export function useAppBootstrap() {
  const testInstallation = computed(() => testInstallationRef.value)

  return { testInstallation }
}
