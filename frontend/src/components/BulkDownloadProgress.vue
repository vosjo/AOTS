<script setup lang="ts">
defineProps<{
  status: string
  busy?: boolean
}>()
</script>

<template>
  <div
    v-if="status || busy"
    class="inline-flex items-center gap-2 text-xs text-aots-muted"
    role="status"
    aria-live="polite"
  >
    <span
      v-if="busy"
      class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-aots border-t-aots-accent"
      aria-hidden="true"
    />
    <span>{{ status || 'Preparing download…' }}</span>
  </div>
</template>
