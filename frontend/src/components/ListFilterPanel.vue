<script setup lang="ts">
import AppButton from '@/components/AppButton.vue'

defineProps<{
  open: boolean
  title?: string
}>()
const emit = defineEmits<{ close: []; apply: []; clear: [] }>()
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 top-14 z-[39] bg-aots-overlay"
    aria-hidden="true"
    @click="emit('close')"
  />
  <aside
    class="fixed inset-y-0 right-0 z-40 top-14 w-80 max-w-full border-l border-aots bg-aots-surface-solid p-4 shadow-2xl transition-transform duration-200"
    :class="open ? 'translate-x-0' : 'translate-x-full'"
  >
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-aots-heading">{{ title ?? 'Filters' }}</h2>
      <AppButton variant="ghost" @click="emit('close')">Close</AppButton>
    </div>
    <form class="space-y-4" @submit.prevent="emit('apply')">
      <slot />
      <div class="grid grid-cols-2 gap-2">
        <AppButton type="button" variant="secondary" @click="emit('clear')">Clear filters</AppButton>
        <AppButton type="submit" variant="primary">Apply filters</AppButton>
      </div>
    </form>
  </aside>
</template>
