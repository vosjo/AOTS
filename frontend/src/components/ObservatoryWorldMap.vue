<script setup lang="ts">
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { onMounted, onUnmounted, ref, watch } from 'vue'

export interface ObservatoryMapPoint {
  pk: number
  name: string
  latitude: number
  longitude: number
}

const props = defineProps<{
  observatories: ObservatoryMapPoint[]
}>()

const mapEl = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markerLayer: L.LayerGroup | null = null

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

  for (const obs of props.observatories) {
    const lat = obs.latitude
    const lon = obs.longitude
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue

    const latlng: L.LatLngTuple = [lat, lon]

    const marker = L.circleMarker(latlng, {
      radius: 7,
      color: '#7dd3fc',
      fillColor: '#0ea5e9',
      fillOpacity: 0.9,
      weight: 2,
    })
    marker.bindPopup(`<strong>${escapeHtml(obs.name)}</strong>`)
    markerLayer.addLayer(marker)
  }
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

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20,
  }).addTo(map)

  markerLayer = L.layerGroup().addTo(map)
  rebuildMarkers()
  showWorldView()

  requestAnimationFrame(() => {
    map?.invalidateSize()
    showWorldView()
  })
})

watch(() => props.observatories, rebuildMarkers, { deep: true })

onUnmounted(() => {
  map?.remove()
  map = null
  markerLayer = null
})
</script>

<template>
  <div class="observatory-world-map w-full">
    <div ref="mapEl" class="observatory-world-map__viewport" />
    <p v-if="observatories.length === 0" class="mt-2 text-sm text-slate-400">
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
  border: 1px solid rgb(100 116 139);
  background: #0f172a;
}

.observatory-world-map :deep(.leaflet-control-attribution) {
  font-size: 0.65rem;
  background: rgb(15 23 42 / 0.85);
  color: rgb(148 163 184);
}

.observatory-world-map :deep(.leaflet-control-attribution a) {
  color: rgb(125 211 252);
}

.observatory-world-map :deep(.leaflet-popup-content-wrapper) {
  background: rgb(30 41 59);
  color: rgb(241 245 249);
  border-radius: 0.375rem;
}

.observatory-world-map :deep(.leaflet-popup-tip) {
  background: rgb(30 41 59);
}
</style>
