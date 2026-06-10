<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import BokehPlot from '@/components/BokehPlot.vue'
import { api } from '@/api/client'

const route = useRoute()
const slug = computed(() => route.params.projectSlug as string)
const hrdParams = ref<Record<string, string>>({})

const { data, isFetching, refetch } = useQuery({
  queryKey: computed(() => ['dashboard', slug.value, hrdParams.value]),
  queryFn: async () => {
    const params = new URLSearchParams(hrdParams.value)
    return api<{
      stats: Record<string, number>
      recent_changes: Array<{ modeltype: string; date: string; user: string; label: string; created: boolean }>
      hrd: { script: string; div: string }
      hrd_form: { fields: string[]; values: Record<string, string>; choices: Record<string, [string, string][]> }
      starmap: { preview_url: string | null; full_url: string | null }
    }>(`/api/dash/${slug.value}/?${params}`)
  },
})

const form = computed(() => data.value?.hrd_form)
const starmapOpen = ref(false)

function updateHrd() {
  if (form.value) hrdParams.value = { ...form.value.values }
  refetch()
}
</script>

<template>
  <div v-if="isFetching && !data" class="text-slate-300">Loading dashboard…</div>
  <div v-else-if="data" class="space-y-6">
    <h1 class="text-2xl font-semibold">Dashboard</h1>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="(val, key) in data.stats" :key="key" class="aots-panel">
        <div class="text-2xl font-semibold">{{ val }}</div>
        <div class="text-xs font-medium uppercase text-slate-300">{{ key }}</div>
      </div>
    </div>

    <div class="grid gap-6 lg:grid-cols-3">
      <section class="aots-panel space-y-3">
        <h2 class="font-medium">HRD controls</h2>
        <div v-if="form" class="space-y-2 text-sm">
          <label v-for="field in form.fields" :key="field" class="block">
            <span class="aots-label capitalize">{{ field }}</span>
            <select
              v-model="form.values[field]"
              class="aots-select"
            >
              <option v-for="[val, label] in form.choices[field]" :key="String(val)" :value="val ?? ''">{{ label }}</option>
            </select>
          </label>
          <button class="aots-btn-primary" @click="updateHrd">Update Figure</button>
        </div>
      </section>

      <section class="aots-panel lg:col-span-2">
        <BokehPlot v-if="data.hrd" :script="data.hrd.script" :div="data.hrd.div" />
      </section>
    </div>

    <div class="grid gap-6 lg:grid-cols-2">
      <section v-if="data.starmap.preview_url" class="aots-panel">
        <h2 class="font-medium mb-2">Starmap</h2>
        <img
          :src="data.starmap.preview_url"
          alt="Starmap preview"
          class="cursor-pointer max-h-64 rounded"
          @click="starmapOpen = true"
        />
      </section>

      <section class="aots-panel">
        <h2 class="font-medium mb-2">Latest changes</h2>
        <ul class="text-sm space-y-2 max-h-64 overflow-y-auto">
          <li v-for="(c, i) in data.recent_changes" :key="i" class="border-b border-slate-600 pb-2">
            <span class="text-slate-300">{{ c.date.slice(0, 10) }}</span>
            {{ c.created ? 'Created' : 'Updated' }} {{ c.modeltype }} — {{ c.label }}
            <span class="text-slate-500">by {{ c.user }}</span>
          </li>
        </ul>
      </section>
    </div>

    <dialog v-if="starmapOpen && data.starmap.full_url" open class="fixed inset-0 z-50 bg-black/80 p-8" @click="starmapOpen = false">
      <img :src="data.starmap.full_url" alt="Full starmap" class="max-h-full max-w-full mx-auto" @click.stop />
    </dialog>
  </div>
</template>
