<script setup lang="ts">
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useThemeStore } from '@/stores/theme'
import type { ThemeMode } from '@/theme'

export interface ObservatoryMapPoint {
  pk: number
  name: string
  latitude: number
  longitude: number
}

const props = defineProps<{
  observatories: ObservatoryMapPoint[]
}>()

const themeStore = useThemeStore()
const mapEl = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markerLayer: L.LayerGroup | null = null
let tileLayer: L.TileLayer | null = null

const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'

function basemapUrl(mode: ThemeMode) {
  const variant = mode === 'light' ? 'light_all' : 'dark_all'
  return `https://{s}.basemaps.cartocdn.com/${variant}/{z}/{x}/{y}{r}.png`
}

function markerColors() {
  const style = getComputedStyle(document.documentElement)
  return {
    color: style.getPropertyValue('--aots-link-hover').trim() || '#7dd3fc',
    fillColor: style.getPropertyValue('--aots-accent').trim() || '#38bdf8',
  }
}

function showWorldView() {
  if (!map) return
  map.fitWorld({ animate: false, padding: [0, 0] })
  map.setZoom(map.getZoom() + 1, { animate: false })
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function rebuildMarkers() {
  if (!map || !markerLayer) return

  markerLayer.clearLayers()
  const colors = markerColors()

  for (const obs of props.observatories) {
    const lat = obs.latitude
    const lon = obs.longitude
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue

    const latlng: L.LatLngTuple = [lat, lon]

    const marker = L.circleMarker(latlng, {
      radius: 7,
      color: colors.color,
      fillColor: colors.fillColor,
      fillOpacity: 0.9,
      weight: 2,
    })
    marker.bindPopup(`<strong>${escapeHtml(obs.name)}</strong>`)
    markerLayer.addLayer(marker)
  }
}

function applyBasemap(mode: ThemeMode) {
  if (!map) return

  if (tileLayer) {
    map.removeLayer(tileLayer)
  }

  tileLayer = L.tileLayer(basemapUrl(mode), {
    attribution: TILE_ATTRIBUTION,
    subdomains: 'abcd',
    maxZoom: 20,
  }).addTo(map)
  tileLayer.bringToBack()
}

onMounted(() => {
  if (!mapEl.value) return

  map = L.map(mapEl.value, {
    center: [0, 0],
    zoom: 0,
    minZoom: 0,
    maxZoom: 12,
    worldCopyJump: true,
    scrollWheelZoom: true,
  })

  applyBasemap(themeStore.mode)
  markerLayer = L.layerGroup().addTo(map)
  rebuildMarkers()
  showWorldView()

  requestAnimationFrame(() => {
    map?.invalidateSize()
    showWorldView()
  })
})

watch(() => props.observatories, rebuildMarkers, { deep: true })

watch(
  () => themeStore.mode,
  (mode) => {
    applyBasemap(mode)
    rebuildMarkers()
  },
)

onUnmounted(() => {
  map?.remove()
  map = null
  markerLayer = null
  tileLayer = null
})
</script>

<template>
  <div class="observatory-world-map w-full">
    <div ref="mapEl" class="observatory-world-map__viewport" />
    <p v-if="observatories.length === 0" class="mt-2 text-sm text-aots-muted">
      No ground-based observatories to show.
    </p>
  </div>
</template>

<style scoped>
.observatory-world-map__viewport {
  aspect-ratio: 2 / 1;
  width: 100%;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid var(--aots-border);
  background: var(--aots-surface-muted);
}

.observatory-world-map :deep(.leaflet-container) {
  background: var(--aots-surface-muted);
  font-family: inherit;
}

.observatory-world-map :deep(.leaflet-control-attribution) {
  font-size: 0.65rem;
  background: var(--aots-surface-solid);
  color: var(--aots-text-muted);
  border: 1px solid var(--aots-border-subtle);
  border-radius: 0.25rem;
}

.observatory-world-map :deep(.leaflet-control-attribution a) {
  color: var(--aots-link);
}

.observatory-world-map :deep(.leaflet-popup-content-wrapper) {
  background: var(--aots-surface-solid);
  color: var(--aots-text);
  border: 1px solid var(--aots-border);
  border-radius: 0.375rem;
  box-shadow: 0 4px 12px rgb(0 0 0 / 0.2);
}

.observatory-world-map :deep(.leaflet-popup-content) {
  margin: 0.5rem 0.65rem;
  font-size: 0.8125rem;
  line-height: 1.35;
}

.observatory-world-map :deep(.leaflet-popup-tip) {
  background: var(--aots-surface-solid);
  border: 1px solid var(--aots-border);
  box-shadow: none;
}

.observatory-world-map :deep(.leaflet-popup-close-button) {
  color: var(--aots-text-muted);
}

.observatory-world-map :deep(.leaflet-popup-close-button:hover) {
  color: var(--aots-link);
}
</style>
