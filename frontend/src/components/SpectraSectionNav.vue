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
    <h1 class="text-2xl font-semibold text-slate-50">Spectroscopy</h1>
    <nav
      class="flex flex-wrap gap-1 border-b border-slate-600"
      aria-label="Spectroscopy views"
    >
      <RouterLink
        v-for="tab in tabs"
        :key="tab.id"
        :to="tab.to"
        class="rounded-t-md px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.id
          ? 'border border-b-0 border-slate-600 bg-slate-800 text-slate-50'
          : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'"
        :title="tab.title"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>
  </header>
</template>
