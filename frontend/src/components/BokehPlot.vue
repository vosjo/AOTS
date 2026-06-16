<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { embedBokehComponents, resizeBokehIn } from '@/composables/useBokeh'

const props = withDefaults(
  defineProps<{
    script: string
    div: string
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

async function render() {
  error.value = null
  if (!host.value || !props.script || !props.div) return
  try {
    await embedBokehComponents(host.value, props.div, props.script)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Plot failed to render'
    console.error('Bokeh embed error:', e)
  }
}

watch(() => [props.script, props.div], render)

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
    <p v-if="error" class="text-sm text-red-400 mt-2">{{ error }}</p>
  </div>
</template>
