<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import AppAlert from '@/components/AppAlert.vue'

const props = withDefaults(
  defineProps<{
    ra: number
    dec: number
    fov?: number
    compact?: boolean
    vizierCatalog?: string
  }>(),
  { compact: false, fov: undefined, vizierCatalog: undefined },
)

const el = ref<HTMLElement | null>(null)
const error = ref<string | null>(null)
let aladin: { destroy?: () => void; addCatalog?: (cat: unknown) => void } | null = null

onMounted(async () => {
  if (!el.value) return
  error.value = null
  try {
    const A = (await import('aladin-lite')).default
    await A.init
    const fov = props.fov ?? (props.compact ? 1.01 / 60 : 0.5)
    aladin = A.aladin(el.value, {
      survey: 'P/DSS2/color',
      fov,
      target: `${props.ra} ${props.dec}`,
      showReticle: true,
      showFullscreenControl: !props.compact,
      showZoomControl: !props.compact,
      showLayersControl: !props.compact,
      showGotoControl: !props.compact,
      showFrame: !props.compact,
      showStatusBar: !props.compact,
      showCooLocation: !props.compact,
      showFov: !props.compact,
      reticleSize: props.compact ? 14 : 22,
    })
    if (props.vizierCatalog && aladin?.addCatalog) {
      const cat = A.catalogFromVizieR(
        props.vizierCatalog,
        `${props.ra} ${props.dec}`,
        fov,
        { onClick: 'showTable' },
      )
      aladin.addCatalog(cat)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Aladin Lite failed to load'
    console.error('Aladin Lite error:', e)
  }
})

onUnmounted(() => {
  aladin?.destroy?.()
  if (el.value) el.value.innerHTML = ''
  aladin = null
})
</script>

<template>
  <div
    class="aladin-map"
    :class="{ 'aladin-map--compact': compact }"
  >
    <div
      ref="el"
      class="aladin-map__viewport w-full rounded-lg border border-aots overflow-hidden relative"
      :class="compact ? 'h-44' : 'h-80'"
    />
    <AppAlert
      v-if="error"
      kind="error"
      class="mt-2"
    >
      {{ error }}
    </AppAlert>
  </div>
</template>

<style scoped>
.aladin-map--compact :deep(.aladin-container) {
  font-size: 0.65rem;
}

.aladin-map--compact :deep(.aladin-view-label) {
  font-size: 0.65rem;
}

.aladin-map--compact :deep(.aladin-fov) {
  line-height: 1.1rem;
}

/* Fallback: hide fetch progress if status bar is ever enabled */
.aladin-map--compact :deep(.aladin-status-bar) {
  display: none !important;
}
</style>
