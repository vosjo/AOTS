<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import { projectLogoUrl } from '@/api/client'
import { useAppBootstrap } from '@/composables/useAppBootstrap'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()
const { testInstallation } = useAppBootstrap()

const sections = computed(() => [
  {
    title: 'Private projects',
    projects: projectStore.projects.filter((project) => !project.is_public),
  },
  {
    title: 'Public projects',
    projects: projectStore.projects.filter((project) => project.is_public),
  },
])

onMounted(() => projectStore.fetchProjects())
</script>

<template>
  <div class="space-y-6">
    <AppAlert v-if="testInstallation" kind="warning" centered>
      This is a test installation. Data may be incomplete or reset at any time.
    </AppAlert>

    <h1 class="text-2xl font-semibold">Projects</h1>

    <section
      v-for="section in sections"
      :key="section.title"
      v-show="section.projects.length"
      class="space-y-3"
    >
      <h2 class="text-lg font-medium text-aots">{{ section.title }}</h2>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <RouterLink
          v-for="project in section.projects"
          :key="project.slug"
          :to="`/w/${project.slug}/dash/`"
          class="flex flex-col rounded-lg border border-aots bg-aots-surface px-2 py-2 shadow-sm transition hover:border-aots-card hover:bg-aots-surface-muted"
        >
          <h3 class="text-center text-base font-medium leading-snug">{{ project.name }}</h3>
          <div class="mt-2 flex min-h-36 flex-1 items-start justify-center">
            <img
              :src="projectLogoUrl(project)"
              :alt="`${project.name} logo`"
              class="block h-36 w-full object-contain"
            />
          </div>
          <p
            v-if="project.description"
            class="mt-1 line-clamp-2 text-center text-sm italic leading-snug text-aots-muted"
          >
            {{ project.description }}
          </p>
        </RouterLink>
      </div>
    </section>
  </div>
</template>
