<script setup lang="ts">
import AppAlert from '@/components/AppAlert.vue'

defineProps<{
  success?: string | null
  error?: string | null
}>()
</script>

<template>
  <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:gap-4">
    <div class="flex flex-wrap gap-3">
      <slot />
    </div>
    <div v-if="success || error" class="w-full lg:ml-auto lg:max-w-lg lg:flex-1">
      <AppAlert v-if="success" kind="success">{{ success }}</AppAlert>
      <AppAlert v-else-if="error" kind="error">{{ error }}</AppAlert>
    </div>
  </div>
</template>
