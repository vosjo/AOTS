<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import SystemsSectionNav from '@/components/SystemsSectionNav.vue'
import { api, formatApiError } from '@/api/client'
import { useProjectStore } from '@/stores/project'
import { useProjectPermissions } from '@/composables/useProjectPermissions'

const route = useRoute()
const projectStore = useProjectStore()
const { canAdd } = useProjectPermissions()

const projectSlug = computed(() => route.params.projectSlug as string)
const selectedFile = ref<File | null>(null)
const busy = ref(false)
const message = ref('')
const messageKind = ref<'success' | 'error'>('success')
const resultSummary = ref<Record<string, number> | null>(null)
const warnings = ref<string[]>([])

async function pollTask(taskId: string) {
  for (let i = 0; i < 120; i++) {
    const status = await api<{ status: string }>(`/api/interop/astra/import/${taskId}/`)
    if (status.status === 'SUCCESS' || status.status === 'success') {
      return await api<{
        summary: Record<string, number>
        warnings: string[]
      }>(`/api/interop/astra/import/${taskId}/result/`)
    }
    if (status.status === 'FAILURE' || status.status === 'failure') {
      throw new Error('Import task failed')
    }
    await new Promise((r) => setTimeout(r, 1000))
  }
  throw new Error('Import timed out')
}

async function startImport() {
  const project = projectStore.currentProject
  if (!selectedFile.value || !project) return
  busy.value = true
  message.value = ''
  resultSummary.value = null
  warnings.value = []
  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    fd.append('project', String(project.pk))
    const { task_id } = await api<{ task_id: string }>('/api/interop/astra/import/?async=1', {
      method: 'POST',
      body: fd,
    })
    const result = await pollTask(task_id)
    resultSummary.value = result.summary
    warnings.value = result.warnings ?? []
    messageKind.value = 'success'
    message.value = 'ASTRA package imported successfully.'
  } catch (e) {
    messageKind.value = 'error'
    message.value = formatApiError(e)
  } finally {
    busy.value = false
  }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}
</script>

<template>
  <div class="space-y-6">
    <SystemsSectionNav />

    <section class="aots-panel max-w-xl space-y-4">
      <h2 class="text-lg font-medium">Import ASTRA package</h2>
      <p class="text-sm text-aots-muted">
        Upload a <code>.astra</code> file exported from ASTRA. Stars, spectra, light curves,
        and analyses are merged into this project.
      </p>

      <div v-if="!canAdd" class="text-sm text-aots-muted">
        You need write access to import data.
      </div>

      <template v-else>
        <input
          type="file"
          accept=".astra"
          class="block w-full text-sm"
          @change="onFileChange"
        />
        <AppButton
          variant="primary"
          :disabled="busy || !selectedFile"
          @click="startImport"
        >
          {{ busy ? 'Importing…' : 'Import' }}
        </AppButton>
      </template>

      <AppAlert v-if="message" :kind="messageKind">{{ message }}</AppAlert>

      <ul v-if="resultSummary" class="text-sm space-y-1">
        <li v-for="(count, key) in resultSummary" :key="key">
          {{ key }}: {{ count }}
        </li>
      </ul>

      <AppAlert v-for="(warn, idx) in warnings" :key="idx" kind="warning">
        {{ warn }}
      </AppAlert>

      <RouterLink
        :to="`/w/${projectSlug}/systems/stars/`"
        class="text-sm text-aots-brand hover:underline"
      >
        Back to stars
      </RouterLink>
    </section>
  </div>
</template>
