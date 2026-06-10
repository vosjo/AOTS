<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'

const pk = computed(() => useRoute().params.id as string)

const { data: dataset } = useQuery({
  queryKey: computed(() => ['dataset', pk.value]),
  queryFn: () => api<Record<string, unknown>>(`/api/analysis/datasets/${pk.value}/`),
})

const { data: plots } = useQuery({
  queryKey: computed(() => ['dataset-plots', pk.value]),
  queryFn: () => api<Record<string, { script: string; div: string }>>(`/api/analysis/datasets/${pk.value}/plots/`),
})
</script>

<template>
  <div v-if="dataset" class="space-y-6">
    <h1 class="text-2xl font-semibold">{{ dataset.name }}</h1>
    <p class="text-sm text-slate-400">Valid: {{ dataset.valid }}</p>
    <div v-if="plots" class="space-y-6">
      <section v-for="(embed, key) in plots" :key="key" class="aots-panel">
        <h2 class="font-medium mb-2 capitalize">{{ key }}</h2>
        <BokehPlot :script="embed.script" :div="embed.div" />
      </section>
    </div>
  </div>
</template>
