import { onUnmounted, ref } from 'vue'
import { formatApiError } from '@/api/client'

export function useAdminFormFeedback() {
  const error = ref<string | null>(null)
  const success = ref<string | null>(null)
  let successTimer: ReturnType<typeof setTimeout> | undefined

  function clearSuccessTimer() {
    if (successTimer) {
      clearTimeout(successTimer)
      successTimer = undefined
    }
  }

  function showSuccess(message: string) {
    error.value = null
    success.value = message
    clearSuccessTimer()
    successTimer = setTimeout(() => {
      success.value = null
    }, 4000)
  }

  function showError(err: unknown) {
    clearSuccessTimer()
    success.value = null
    error.value = formatApiError(err)
  }

  function clearMessages() {
    clearSuccessTimer()
    error.value = null
    success.value = null
  }

  onUnmounted(clearSuccessTimer)

  return { error, success, showSuccess, showError, clearMessages }
}
