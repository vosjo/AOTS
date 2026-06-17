<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const projectSlug = computed(() => route.params.projectSlug as string)

const tabs = computed(() => [
  {
    id: 'spectra',
    label: 'Spectra',
    to: `/w/${projectSlug.value}/observations/spectra/`,
    names: ['spectra'],
  },
  {
    id: 'raw',
    label: 'Raw data',
    to: `/w/${projectSlug.value}/observations/spectra/raw/`,
    names: ['spectra-raw'],
  },
  {
    id: 'files',
    label: 'File index',
    to: `/w/${projectSlug.value}/observations/spectra/files/`,
    names: ['spectra-files'],
    title: 'Reduced spectrum files (advanced)',
  },
])

const activeTab = computed(() => {
  const name = route.name
  if (typeof name !== 'string') return 'spectra'
  if (name === 'spectra-raw') return 'raw'
  if (name === 'spectra-files') return 'files'
  return 'spectra'
})
</script>

<template>
  <header class="space-y-3">
    <h1 class="text-2xl font-semibold text-aots-heading">Spectroscopy</h1>
    <nav class="aots-section-nav" aria-label="Spectroscopy views">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.id"
        :to="tab.to"
        class="aots-section-tab"
        :class="{ 'aots-section-tab--active': activeTab === tab.id }"
        :title="tab.title"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>
  </header>
</template>
