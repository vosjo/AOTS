<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import UserMultiSelect from '@/components/admin/UserMultiSelect.vue'
import { api } from '@/api/client'
import { useAdminEntityRoute } from '@/composables/useAdminEntityRoute'
import { useAdminFormFeedback } from '@/composables/useAdminFormFeedback'
import AdminFormActions from '@/components/admin/AdminFormActions.vue'
import AppButton from '@/components/AppButton.vue'

interface AdminProject {
  pk: number
  name: string
  slug: string
  description: string
  is_public: boolean
  logo: string | null
  preview_starmap: string | null
  full_starmap: string | null
  readonly_users: number[]
  readwriteown_users: number[]
  readwrite_users: number[]
  project_managers: number[]
}

const router = useRouter()
const { isNew, entityId: projectId } = useAdminEntityRoute()
const { error, success, showSuccess, showError, clearMessages } = useAdminFormFeedback()

const loading = ref(false)
const saving = ref(false)

const name = ref('')
const slug = ref('')
const description = ref('')
const isPublic = ref(true)
const logoUrl = ref<string | null>(null)
const previewUrl = ref<string | null>(null)
const fullUrl = ref<string | null>(null)
const logoFile = ref<File | null>(null)
const previewFile = ref<File | null>(null)
const fullFile = ref<File | null>(null)
const readonlyUsers = ref<number[]>([])
const readwriteownUsers = ref<number[]>([])
const readwriteUsers = ref<number[]>([])
const projectManagers = ref<number[]>([])

async function loadProject() {
  if (!projectId.value) return
  loading.value = true
  clearMessages()
  try {
    applyProject(await api<AdminProject>(`/api/admin/projects/${projectId.value}/`))
  } catch (err) {
    showError(err)
  } finally {
    loading.value = false
  }
}

function applyProject(project: AdminProject) {
  name.value = project.name
  slug.value = project.slug
  description.value = project.description
  isPublic.value = project.is_public
  logoUrl.value = project.logo
  previewUrl.value = project.preview_starmap
  fullUrl.value = project.full_starmap
  readonlyUsers.value = project.readonly_users
  readwriteownUsers.value = project.readwriteown_users
  readwriteUsers.value = project.readwrite_users
  projectManagers.value = project.project_managers
}

function buildFormData(): FormData {
  const form = new FormData()
  form.append('name', name.value)
  form.append('description', description.value)
  form.append('is_public', String(isPublic.value))
  if (isNew.value && slug.value) form.append('slug', slug.value)
  form.append('readonly_users', JSON.stringify(readonlyUsers.value))
  form.append('readwriteown_users', JSON.stringify(readwriteownUsers.value))
  form.append('readwrite_users', JSON.stringify(readwriteUsers.value))
  form.append('project_managers', JSON.stringify(projectManagers.value))
  if (logoFile.value) form.append('logo', logoFile.value)
  if (previewFile.value) form.append('preview_starmap', previewFile.value)
  if (fullFile.value) form.append('full_starmap', fullFile.value)
  return form
}

async function save() {
  saving.value = true
  clearMessages()
  try {
    const hasFiles = !!(logoFile.value || previewFile.value || fullFile.value)
    if (hasFiles || isNew.value) {
      const form = buildFormData()
      if (isNew.value) {
        const created = await api<AdminProject>('/api/admin/projects/', {
          method: 'POST',
          body: form,
        })
        await router.push(`/admin/projects/${created.pk}`)
        return
      }
      const updated = await api<AdminProject>(`/api/admin/projects/${projectId.value}/`, {
        method: 'PATCH',
        body: form,
      })
      applyProject(updated)
    } else {
      const updated = await api<AdminProject>(`/api/admin/projects/${projectId.value}/`, {
        method: 'PATCH',
        body: {
          name: name.value,
          description: description.value,
          is_public: isPublic.value,
          readonly_users: readonlyUsers.value,
          readwriteown_users: readwriteownUsers.value,
          readwrite_users: readwriteUsers.value,
          project_managers: projectManagers.value,
        },
      })
      applyProject(updated)
    }
    logoFile.value = null
    previewFile.value = null
    fullFile.value = null
    showSuccess(`Saved project “${name.value}”.`)
  } catch (err) {
    showError(err)
  } finally {
    saving.value = false
  }
}

async function removeProject() {
  if (!projectId.value) return
  if (!window.confirm('Delete this project and all related data?')) return
  saving.value = true
  clearMessages()
  try {
    await api(`/api/admin/projects/${projectId.value}/`, { method: 'DELETE' })
    await router.push('/admin/projects/')
  } catch (err) {
    showError(err)
  } finally {
    saving.value = false
  }
}

function onFileChange(event: Event, target: 'logo' | 'preview' | 'full') {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  if (target === 'logo') logoFile.value = file
  if (target === 'preview') previewFile.value = file
  if (target === 'full') fullFile.value = file
}

onMounted(loadProject)
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <h2 class="text-xl font-semibold">{{ isNew ? 'Add project' : `Edit project: ${name}` }}</h2>
    <p v-if="loading" class="text-slate-300">Loading…</p>

    <form class="space-y-6" @submit.prevent="save">
      <section class="aots-panel space-y-3">
        <h3 class="font-medium text-slate-50">Basics</h3>
        <input v-model="name" class="aots-field" placeholder="Name" required />
        <input
          v-model="slug"
          class="aots-field"
          placeholder="Slug (auto-generated if empty on create)"
          :readonly="!isNew"
        />
        <textarea v-model="description" class="aots-field min-h-24" placeholder="Description" />
        <label class="flex items-center gap-2 text-sm">
          <input v-model="isPublic" type="checkbox" class="accent-sky-400" />
          Public project
        </label>
      </section>

      <section class="aots-panel space-y-3">
        <h3 class="font-medium text-slate-50">Files</h3>
        <div>
          <label class="text-sm text-slate-300">Logo</label>
          <a v-if="logoUrl" :href="logoUrl" class="block text-sm text-sky-400" target="_blank">Current file</a>
          <input type="file" class="aots-field" @change="onFileChange($event, 'logo')" />
        </div>
        <div>
          <label class="text-sm text-slate-300">Preview starmap</label>
          <a v-if="previewUrl" :href="previewUrl" class="block text-sm text-sky-400" target="_blank">Current file</a>
          <input type="file" class="aots-field" @change="onFileChange($event, 'preview')" />
        </div>
        <div>
          <label class="text-sm text-slate-300">Full starmap</label>
          <a v-if="fullUrl" :href="fullUrl" class="block text-sm text-sky-400" target="_blank">Current file</a>
          <input type="file" class="aots-field" @change="onFileChange($event, 'full')" />
        </div>
      </section>

      <section class="aots-panel grid gap-4 md:grid-cols-2">
        <UserMultiSelect v-model="readonlyUsers" label="Read-only users" />
        <UserMultiSelect v-model="readwriteownUsers" label="Read/write own users" />
        <UserMultiSelect v-model="readwriteUsers" label="Read/write users" />
        <UserMultiSelect v-model="projectManagers" label="Project managers" />
      </section>

      <AdminFormActions :success="success" :error="error">
        <AppButton type="submit" variant="primary" :disabled="saving || loading">
          {{ saving ? 'Saving…' : 'Save' }}
        </AppButton>
        <AppButton variant="ghost" to="/admin/projects/">Cancel</AppButton>
        <AppButton
          v-if="!isNew"
          variant="ghost-danger"
          :disabled="saving"
          @click="removeProject"
        >
          Delete
        </AppButton>
      </AdminFormActions>
    </form>
  </div>
</template>
