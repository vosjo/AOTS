<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const projectSlug = computed(() => route.params.projectSlug as string)

const tabs = computed(() => [
  {
    id: 'stars',
    label: 'Stars',
    to: `/w/${projectSlug.value}/systems/stars/`,
  },
  {
    id: 'tags',
    label: 'Tags',
    to: `/w/${projectSlug.value}/systems/tags/`,
  },
])

const activeTab = computed(() => {
  const name = route.name
  if (typeof name === 'string' && name === 'tags') return 'tags'
  return 'stars'
})
</script>

<template>
  <header class="space-y-3">
    <h1 class="text-2xl font-semibold text-slate-50">Systems</h1>
    <nav
      class="flex flex-wrap gap-1 border-b border-slate-600"
      aria-label="Systems views"
    >
      <RouterLink
        v-for="tab in tabs"
        :key="tab.id"
        :to="tab.to"
        class="rounded-t-md px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.id
          ? 'border border-b-0 border-slate-600 bg-slate-800 text-slate-50'
          : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>
  </header>
</template>
