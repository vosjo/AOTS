import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

export function useProjectPermissions() {
  const auth = useAuthStore()
  const projectStore = useProjectStore()

  const canAdd = computed(() => {
    if (!auth.isAuthenticated) return false
    if (auth.isSuperuser) return true
    return projectStore.currentProject?.can_add === true
  })

  return { canAdd }
}

export function hasObjectPermission(
  value: { can_edit?: boolean; can_delete?: boolean } | null | undefined,
  kind: 'edit' | 'delete',
): boolean {
  if (!value) return false
  return kind === 'edit' ? value.can_edit === true : value.can_delete === true
}
