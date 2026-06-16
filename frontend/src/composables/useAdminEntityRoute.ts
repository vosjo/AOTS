import { computed } from 'vue'
import { useRoute } from 'vue-router'

/** Resolve admin form routes like `/admin/groups/:id` where id is `new` or a numeric pk. */
export function useAdminEntityRoute() {
  const route = useRoute()

  const isNew = computed(() => String(route.params.id ?? '') === 'new')

  const entityId = computed(() => {
    if (isNew.value) return null
    const id = Number(route.params.id)
    return Number.isFinite(id) ? id : null
  })

  return { isNew, entityId }
}
