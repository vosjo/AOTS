<script setup lang="ts">
import { onMounted } from 'vue'
import AppTopBar from '@/components/AppTopBar.vue'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()
onMounted(() => projectStore.fetchProjects())
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppTopBar />
    <main class="flex-1 mx-auto w-full max-w-[1600px] px-4 py-6">
      <slot />
    </main>
  </div>
</template>
