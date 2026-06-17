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
    <h1 class="text-2xl font-semibold text-aots-heading">Systems</h1>
    <nav class="aots-section-nav" aria-label="Systems views">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.id"
        :to="tab.to"
        class="aots-section-tab"
        :class="{ 'aots-section-tab--active': activeTab === tab.id }"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>
  </header>
</template>
