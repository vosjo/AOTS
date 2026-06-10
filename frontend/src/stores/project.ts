import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api, type ProjectSummary } from '@/api/client'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<ProjectSummary[]>([])
  const currentSlug = ref<string | null>(null)

  const currentProject = computed(() =>
    projects.value.find((p) => p.slug === currentSlug.value) ?? null,
  )

  async function fetchProjects() {
    projects.value = await api<ProjectSummary[]>('/api/projects/')
    return projects.value
  }

  async function setCurrentSlug(slug: string) {
    currentSlug.value = slug
  }

  return { projects, currentSlug, currentProject, fetchProjects, setCurrentSlug }
})
