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
    <main class="mx-auto min-w-0 flex-1 w-full max-w-[1600px] overflow-x-hidden px-4 py-6">
      <slot />
    </main>
  </div>
</template>
