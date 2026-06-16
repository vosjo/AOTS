<script setup lang="ts">
import AdminNav from '@/components/AdminNav.vue'
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-semibold text-slate-50">Administration</h1>
      <RouterLink to="/w/projects/" class="text-sm text-sky-400 hover:text-sky-300">
        Back to projects
      </RouterLink>
    </div>
    <AdminNav />
    <RouterView />
  </div>
</template>
