<script setup lang="ts">
defineProps<{
  status: string
  busy?: boolean
}>()
</script>

<template>
  <div
    v-if="status || busy"
    class="inline-flex items-center gap-2 text-xs text-slate-400"
    role="status"
    aria-live="polite"
  >
    <span
      v-if="busy"
      class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-500 border-t-sky-400"
      aria-hidden="true"
    />
    <span>{{ status || 'Preparing download…' }}</span>
  </div>
</template>
