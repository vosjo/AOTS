<script setup lang="ts">
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
    <div
      v-if="success || error"
      class="w-full lg:ml-auto lg:max-w-lg lg:flex-1"
      role="status"
      aria-live="polite"
    >
      <p
        v-if="success"
        class="rounded-md border border-emerald-600/50 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-300"
      >
        {{ success }}
      </p>
      <p
        v-else-if="error"
        class="rounded-md border border-red-600/50 bg-red-950/40 px-3 py-2 text-sm text-red-300"
      >
        {{ error }}
      </p>
    </div>
  </div>
</template>
