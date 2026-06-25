<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import AppAlert from '@/components/AppAlert.vue'
import { embedBokehItem, resizeBokehIn } from '@/composables/useBokeh'
import type { BokehEmbedItem } from '@/types/bokeh'

const props = withDefaults(
  defineProps<{
    item: BokehEmbedItem
    /** When true, the host does not enforce a minimum height (better on narrow screens). */
    compact?: boolean
    /** When true, fill the parent box (used with a fixed-size plot frame). */
    fill?: boolean
  }>(),
  { compact: false, fill: false },
)

const host = ref<HTMLElement | null>(null)
const error = ref<string | null>(null)
let resizeObserver: ResizeObserver | null = null
let renderGeneration = 0

async function render() {
  const generation = ++renderGeneration
  error.value = null
  if (!host.value || !props.item) return
  try {
    await embedBokehItem(host.value, props.item)
    if (generation !== renderGeneration) return
  } catch (e) {
    if (generation !== renderGeneration) return
    error.value = e instanceof Error ? e.message : 'Plot failed to render'
  }
}

watch(() => props.item, render, { deep: true })

onMounted(() => {
  render()
  const el = host.value
  if (!el) return
  resizeObserver = new ResizeObserver(() => {
    if (host.value) resizeBokehIn(host.value)
  })
  resizeObserver.observe(el)
  if (el.parentElement) resizeObserver.observe(el.parentElement)
})

onUnmounted(() => {
  renderGeneration += 1
  resizeObserver?.disconnect()
  if (host.value) host.value.innerHTML = ''
})
</script>

<template>
  <div
    class="bokeh-plot-host flex min-h-0 w-full max-w-full min-w-0 flex-col overflow-hidden"
    :class="fill ? 'h-full' : ''"
  >
    <div
      ref="host"
      class="bokeh-plot min-h-0 w-full"
      :class="fill ? 'h-full flex-1' : compact ? 'min-h-0' : 'min-h-[200px]'"
    />
    <AppAlert v-if="error" kind="error" class="mt-2">{{ error }}</AppAlert>
  </div>
</template>
