<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import { api } from '@/api/client'

const route = useRoute()
const router = useRouter()
const starId = computed(() => route.params.id as string)
const form = ref({ name: '', classification: '', note: '' })

const { data } = useQuery({
  queryKey: computed(() => ['star-edit', starId.value]),
  queryFn: () => api<Record<string, string>>(`/api/systems/stars/${starId.value}/`),
})

watch(data, (d) => {
  if (d) form.value = { name: d.name, classification: d.classification ?? '', note: d.note ?? '' }
}, { immediate: true })

async function save() {
  await api(`/api/systems/stars/${starId.value}/`, { method: 'PATCH', body: form.value })
  router.push(`/w/${route.params.projectSlug}/systems/stars/${starId.value}`)
}
</script>

<template>
  <div class="max-w-lg space-y-4">
    <h1 class="text-2xl font-semibold">Edit system</h1>
    <form class="space-y-3" @submit.prevent="save">
      <input v-model="form.name" class="aots-field" placeholder="Name" />
      <input v-model="form.classification" class="aots-field" placeholder="Classification" />
      <textarea v-model="form.note" class="aots-field" rows="4" placeholder="Note" />
      <AppButton type="submit" variant="primary">Save</AppButton>
    </form>
  </div>
</template>
