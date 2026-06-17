<script setup lang="ts">
import AppButton from '@/components/AppButton.vue'
import AdminNav from '@/components/AdminNav.vue'
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-2xl font-semibold text-aots-heading">Administration</h1>
      <AppButton variant="link" to="/w/projects/">
        Back to projects
      </AppButton>
    </div>
    <AdminNav />
    <RouterView />
  </div>
</template>
