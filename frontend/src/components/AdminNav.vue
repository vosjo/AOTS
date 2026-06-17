<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()

const links = [
  { to: '/admin/', label: 'Overview', exact: true },
  { to: '/admin/users/', label: 'Users' },
  { to: '/admin/projects/', label: 'Projects' },
  { to: '/admin/groups/', label: 'Groups' },
  { to: '/admin/tokens/', label: 'Tokens' },
  { to: '/admin/log/', label: 'Log' },
]

function isActive(link: { to: string; exact?: boolean }) {
  if (link.exact) return route.path === link.to
  return route.path.startsWith(link.to)
}
</script>

<template>
  <nav class="mb-6 flex flex-wrap gap-2 border-b border-aots pb-3">
    <RouterLink
      v-for="link in links"
      :key="link.to"
      :to="link.to"
      class="rounded-md px-3 py-1.5 text-sm font-medium"
      :class="isActive(link)
        ? 'bg-aots-surface-muted text-white ring-1 ring-aots'
        : 'text-aots hover:bg-aots-surface hover:text-white'"
    >
      {{ link.label }}
    </RouterLink>
  </nav>
</template>
