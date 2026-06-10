<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()

onMounted(() => projectStore.fetchProjects())
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-semibold">Projects</h1>
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink
        v-for="project in projectStore.projects"
        :key="project.slug"
        :to="`/w/${project.slug}/dash/`"
        class="block rounded-xl border border-slate-500 bg-slate-800 p-5 shadow-sm transition hover:border-sky-400 hover:bg-slate-700"
      >
        <h2 class="text-lg font-medium">{{ project.name }}</h2>
        <p class="mt-1 text-sm text-slate-300">{{ project.is_public ? 'Public' : 'Private' }}</p>
      </RouterLink>
    </div>
  </div>
</template>
