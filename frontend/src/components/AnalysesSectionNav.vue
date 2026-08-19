<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const projectSlug = computed(() => route.params.projectSlug as string)

const tabs = computed(() => [
  {
    id: 'analyses',
    label: 'Analyses',
    to: `/w/${projectSlug.value}/analysis/analyses/`,
  },
  {
    id: 'plotter',
    label: 'Parameter plotter',
    to: `/w/${projectSlug.value}/analysis/analyses/plotter`,
  },
])

const activeTab = computed(() => {
  const name = route.name
  if (typeof name === 'string' && name === 'analysis-plotter') return 'plotter'
  return 'analyses'
})
</script>

<template>
  <header class="space-y-3">
    <h1 class="text-2xl font-semibold text-aots-heading">
      Analyses
    </h1>
    <nav
      class="aots-section-nav"
      aria-label="Analyses views"
    >
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
