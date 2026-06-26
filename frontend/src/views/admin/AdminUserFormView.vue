<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { confirmAction } from '@/composables/useConfirm'
import { useAdminEntityRoute } from '@/composables/useAdminEntityRoute'
import { useAdminFormFeedback } from '@/composables/useAdminFormFeedback'
import AdminFormActions from '@/components/admin/AdminFormActions.vue'
import AppButton from '@/components/AppButton.vue'

interface AdminUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  note: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  is_student: boolean
}

const router = useRouter()
const { isNew, entityId: userId } = useAdminEntityRoute()
const { error, success, showSuccess, showError, clearMessages } = useAdminFormFeedback()

const loading = ref(false)
const saving = ref(false)

const username = ref('')
const email = ref('')
const password = ref('')
const firstName = ref('')
const lastName = ref('')
const note = ref('')
const isActive = ref(true)
const isStaff = ref(false)
const isSuperuser = ref(false)
const isStudent = ref(false)

function applyUser(user: AdminUser) {
  username.value = user.username
  email.value = user.email
  firstName.value = user.first_name
  lastName.value = user.last_name
  note.value = user.note
  isActive.value = user.is_active
  isStaff.value = user.is_staff
  isSuperuser.value = user.is_superuser
  isStudent.value = user.is_student
}

async function loadUser() {
  if (!userId.value) return
  loading.value = true
  clearMessages()
  try {
    applyUser(await api<AdminUser>(`/api/admin/users/${userId.value}/`))
  } catch (err) {
    showError(err)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  clearMessages()
  const payload: Record<string, unknown> = {
    username: username.value,
    email: email.value,
    first_name: firstName.value,
    last_name: lastName.value,
    note: note.value,
    is_active: isActive.value,
    is_staff: isStaff.value,
    is_superuser: isSuperuser.value,
    is_student: isStudent.value,
  }
  if (password.value) payload.password = password.value
  try {
    if (isNew.value) {
      if (!password.value) {
        error.value = 'Password is required for new users.'
        return
      }
      const created = await api<AdminUser>('/api/admin/users/', {
        method: 'POST',
        body: payload,
      })
      await router.push(`/admin/users/${created.id}`)
    } else {
      const updated = await api<AdminUser>(`/api/admin/users/${userId.value}/`, {
        method: 'PATCH',
        body: payload,
      })
      applyUser(updated)
      password.value = ''
      showSuccess(`Saved changes for “${updated.username}”.`)
    }
  } catch (err) {
    showError(err)
  } finally {
    saving.value = false
  }
}

async function removeUser() {
  if (!userId.value) return
  if (!(await confirmAction({
    title: 'Delete user',
    message: 'Delete this user permanently?',
  }))) return
  saving.value = true
  clearMessages()
  try {
    await api(`/api/admin/users/${userId.value}/`, { method: 'DELETE' })
    await router.push('/admin/users/')
  } catch (err) {
    showError(err)
  } finally {
    saving.value = false
  }
}

onMounted(loadUser)
</script>

<template>
  <div class="mx-auto max-w-2xl space-y-6">
    <h2 class="text-xl font-semibold">{{ isNew ? 'Add user' : `Edit user: ${username}` }}</h2>
    <p v-if="loading" class="text-aots-muted">Loading…</p>

    <form class="space-y-6" @submit.prevent="save">
      <section class="aots-panel space-y-3">
        <h3 class="font-medium text-aots-heading">Credentials</h3>
        <input v-model="username" class="aots-field" placeholder="Username" required />
        <input v-model="email" class="aots-field" type="email" placeholder="Email" />
        <input
          v-model="password"
          class="aots-field"
          type="password"
          :placeholder="isNew ? 'Password' : 'New password (leave blank to keep)'"
          :required="isNew"
        />
      </section>

      <section class="aots-panel space-y-3">
        <h3 class="font-medium text-aots-heading">Extra info</h3>
        <input v-model="firstName" class="aots-field" placeholder="First name" />
        <input v-model="lastName" class="aots-field" placeholder="Last name" />
        <textarea v-model="note" class="aots-field min-h-24" placeholder="Note" />
      </section>

      <section class="aots-panel space-y-2">
        <h3 class="font-medium text-aots-heading">Permissions</h3>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="isSuperuser" type="checkbox" class="accent-aots" />
          Superuser
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="isStaff" type="checkbox" class="accent-aots" />
          Staff (Django admin access)
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="isActive" type="checkbox" class="accent-aots" />
          Active
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="isStudent" type="checkbox" class="accent-aots" />
          Student
        </label>
      </section>

      <AdminFormActions :success="success" :error="error">
        <AppButton type="submit" variant="primary" :disabled="saving || loading">
          {{ saving ? 'Saving…' : 'Save' }}
        </AppButton>
        <AppButton variant="ghost" to="/admin/users/">Cancel</AppButton>
        <AppButton
          v-if="!isNew"
          variant="ghost-danger"
          :disabled="saving"
          @click="removeUser"
        >
          Delete
        </AppButton>
      </AdminFormActions>
    </form>
  </div>
</template>
