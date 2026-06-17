<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PermissionDualList, { type PermissionOption } from '@/components/admin/PermissionDualList.vue'
import { api } from '@/api/client'
import { useAdminEntityRoute } from '@/composables/useAdminEntityRoute'
import { useAdminFormFeedback } from '@/composables/useAdminFormFeedback'
import AdminFormActions from '@/components/admin/AdminFormActions.vue'
import AppButton from '@/components/AppButton.vue'

interface PermissionGroup {
  app_label: string
  model: string
  permissions: { id: number; codename: string; name: string }[]
}

interface AdminGroup {
  id: number
  name: string
  permissions: number[]
}

const router = useRouter()
const { isNew, entityId: groupId } = useAdminEntityRoute()
const { error, success, showSuccess, showError, clearMessages } = useAdminFormFeedback()

const loading = ref(false)
const saving = ref(false)
const name = ref('')
const selectedPermissions = ref<number[]>([])
const allPermissions = ref<PermissionOption[]>([])

async function loadPermissions() {
  const groups = await api<PermissionGroup[]>('/api/admin/permissions/')
  allPermissions.value = groups.flatMap((group) =>
    group.permissions.map((perm) => ({
      ...perm,
      app_label: group.app_label,
      model: group.model,
    })),
  )
}

async function loadGroup() {
  if (!groupId.value) return
  loading.value = true
  clearMessages()
  try {
    const group = await api<AdminGroup>(`/api/admin/groups/${groupId.value}/`)
    name.value = group.name
    selectedPermissions.value = [...group.permissions]
  } catch (err) {
    showError(err)
  } finally {
    loading.value = false
  }
}

const permissionsLoading = computed(() => !allPermissions.value.length && !error.value)

async function save() {
  saving.value = true
  clearMessages()
  const payload = {
    name: name.value,
    permissions: selectedPermissions.value,
  }
  try {
    if (isNew.value) {
      const created = await api<AdminGroup>('/api/admin/groups/', {
        method: 'POST',
        body: payload,
      })
      await router.push(`/admin/groups/${created.id}`)
    } else {
      const updated = await api<AdminGroup>(`/api/admin/groups/${groupId.value}/`, {
        method: 'PATCH',
        body: payload,
      })
      name.value = updated.name
      selectedPermissions.value = [...updated.permissions]
      showSuccess(`Saved group “${updated.name}”.`)
    }
  } catch (err) {
    showError(err)
  } finally {
    saving.value = false
  }
}

async function removeGroup() {
  if (!groupId.value) return
  if (!window.confirm('Delete this group?')) return
  saving.value = true
  clearMessages()
  try {
    await api(`/api/admin/groups/${groupId.value}/`, { method: 'DELETE' })
    await router.push('/admin/groups/')
  } catch (err) {
    showError(err)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadPermissions()
  await loadGroup()
})
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-6">
    <h2 class="text-xl font-semibold">{{ isNew ? 'Add group' : `Edit group: ${name}` }}</h2>
    <p v-if="loading" class="text-aots-muted">Loading…</p>

    <form class="space-y-6" @submit.prevent="save">
      <section class="aots-panel space-y-3">
        <input v-model="name" class="aots-field max-w-md" placeholder="Group name" required />
      </section>

      <section class="aots-panel space-y-3">
        <h3 class="font-medium text-aots-heading">Permissions</h3>
        <p v-if="permissionsLoading" class="text-sm text-aots-muted">Loading permissions…</p>
        <PermissionDualList
          v-else
          v-model="selectedPermissions"
          :permissions="allPermissions"
        />
      </section>

      <AdminFormActions :success="success" :error="error">
        <AppButton type="submit" variant="primary" :disabled="saving || loading">
          {{ saving ? 'Saving…' : 'Save' }}
        </AppButton>
        <AppButton variant="ghost" to="/admin/groups/">Cancel</AppButton>
        <AppButton
          v-if="!isNew"
          variant="ghost-danger"
          :disabled="saving"
          @click="removeGroup"
        >
          Delete
        </AppButton>
      </AdminFormActions>
    </form>
  </div>
</template>
