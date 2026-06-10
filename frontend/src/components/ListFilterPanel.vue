<script setup lang="ts">
defineProps<{
  open: boolean
  title?: string
}>()
const emit = defineEmits<{ close: []; apply: []; clear: [] }>()
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 top-14 z-[39] bg-black/40"
    aria-hidden="true"
    @click="emit('close')"
  />
  <aside
    class="fixed inset-y-0 right-0 z-40 top-14 w-80 max-w-full border-l border-slate-500 bg-slate-800 p-4 shadow-2xl transition-transform duration-200"
    :class="open ? 'translate-x-0' : 'translate-x-full'"
  >
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-slate-50">{{ title ?? 'Filters' }}</h2>
      <button type="button" class="aots-btn-ghost" @click="emit('close')">Close</button>
    </div>
    <form class="space-y-4" @submit.prevent="emit('apply')">
      <slot />
      <div class="grid grid-cols-2 gap-2">
        <button type="button" class="aots-btn-secondary" @click="emit('clear')">Clear filters</button>
        <button type="submit" class="aots-btn-primary">Apply filters</button>
      </div>
    </form>
  </aside>
</template>
