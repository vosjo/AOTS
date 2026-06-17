<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api/client'

const route = useRoute()
const userId = computed(() => route.params.id)

const { data } = useQuery({
  queryKey: ['user-profile', userId],
  queryFn: () => api<{ username: string; note: string }>(`/api/users/${userId.value}/`),
})
</script>

<template>
  <div v-if="data" class="space-y-4">
    <h1 class="text-2xl font-semibold">{{ data.username }}</h1>
    <p class="text-aots-muted whitespace-pre-wrap">{{ data.note || 'No profile note.' }}</p>
  </div>
</template>
