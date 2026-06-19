<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

interface PolicyRow {
  id: number
  name: string
  component: number
  rule: string
  preferred_source: number | null
  preferred_source_name: string
  preferred_analysis_category: string
  source_priority: Array<number | string>
  fallback_rule: string
  fallback_preferred_source: number | null
  fallback_preferred_source_name: string
  fallback_analysis_category: string
  priority: number
}

interface FormChoice {
  value: string
  label: string
}

interface FormChoiceGroup {
  group: string
  options: FormChoice[]
}

type ParameterChoiceEntry = FormChoice | FormChoiceGroup

function isChoiceGroup(entry: ParameterChoiceEntry): entry is FormChoiceGroup {
  return 'group' in entry && Array.isArray((entry as FormChoiceGroup).options)
}

function flattenParameterChoices(entries: ParameterChoiceEntry[]): FormChoice[] {
  const out: FormChoice[] = []
  for (const entry of entries) {
    if (isChoiceGroup(entry)) {
      out.push(...entry.options)
    } else {
      out.push(entry)
    }
  }
  return out
}

interface Meta {
  parameter_names: string[]
  parameter_choices: ParameterChoiceEntry[]
  wildcard: string
  sources: Array<{ id: number; name: string; kind: string }>
  analysis_categories: Array<{ value: string; label: string }>
  components: Array<{ value: number; label: string }>
  rules: Array<{ value: string; label: string }>
}

const route = useRoute()
const auth = useAuthStore()
const slug = computed(() => route.params.projectSlug as string)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const policies = ref<PolicyRow[]>([])
const meta = ref<Meta | null>(null)

const editorOpen = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '*',
  component: 0,
  rule: 'weighted_average',
  preferred_source: null as number | null,
  preferred_analysis_category: '',
  source_priority: '' as string,
  fallback_rule: '',
  fallback_preferred_source: null as number | null,
  fallback_analysis_category: '',
  priority: 0,
})

const canEdit = computed(() => auth.isAuthenticated)

function apiBase() {
  return `/api/analysis/consensus-policies/${slug.value}`
}

function resetForm() {
  form.name = '*'
  form.component = 0
  form.rule = 'weighted_average'
  form.preferred_source = null
  form.preferred_analysis_category = ''
  form.source_priority = ''
  form.fallback_rule = ''
  form.fallback_preferred_source = null
  form.fallback_analysis_category = ''
  form.priority = 0
  editingId.value = null
}

function openCreate() {
  resetForm()
  editorOpen.value = true
}

function openEdit(row: PolicyRow) {
  editingId.value = row.id
  form.name = row.name
  form.component = row.component
  form.rule = row.rule
  form.preferred_source = row.preferred_source
  form.preferred_analysis_category = row.preferred_analysis_category || ''
  form.source_priority = (row.source_priority || []).join(', ')
  form.fallback_rule = row.fallback_rule || ''
  form.fallback_preferred_source = row.fallback_preferred_source
  form.fallback_analysis_category = row.fallback_analysis_category || ''
  form.priority = row.priority
  editorOpen.value = true
}

function parsePriority(raw: string): Array<number | string> {
  return raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .map((entry) => {
      const n = Number(entry)
      return Number.isInteger(n) && String(n) === entry ? n : entry
    })
}

function payloadFromForm() {
  return {
    name: form.name,
    component: form.component,
    rule: form.rule,
    preferred_source: form.preferred_source,
    preferred_analysis_category: form.preferred_analysis_category || '',
    source_priority: parsePriority(form.source_priority),
    fallback_rule: form.fallback_rule || '',
    fallback_preferred_source: form.fallback_preferred_source,
    fallback_analysis_category: form.fallback_analysis_category || '',
    priority: form.priority,
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [policyRows, metaRows] = await Promise.all([
      api<PolicyRow[]>(`${apiBase()}/`),
      api<Meta>(`${apiBase()}/meta/`),
    ])
    policies.value = policyRows
    meta.value = metaRows
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load policies'
  } finally {
    loading.value = false
  }
}

async function savePolicy() {
  if (!canEdit.value) return
  saving.value = true
  error.value = ''
  try {
    const body = payloadFromForm()
    if (editingId.value) {
      await api(`${apiBase()}/${editingId.value}/`, { method: 'PATCH', body })
    } else {
      await api(`${apiBase()}/`, { method: 'POST', body })
    }
    editorOpen.value = false
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save policy'
  } finally {
    saving.value = false
  }
}

async function deletePolicy(row: PolicyRow) {
  if (!canEdit.value) return
  if (!window.confirm(`Delete policy for ${row.name} (component ${row.component})?`)) return
  saving.value = true
  error.value = ''
  try {
    await api(`${apiBase()}/${row.id}/`, { method: 'DELETE' })
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to delete policy'
  } finally {
    saving.value = false
  }
}

function ruleLabel(value: string) {
  return meta.value?.rules.find((r) => r.value === value)?.label ?? value
}

function componentLabel(value: number) {
  return meta.value?.components.find((c) => c.value === value)?.label ?? String(value)
}

function parameterLabel(value: string) {
  return flattenParameterChoices(meta.value?.parameter_choices ?? []).find((p) => p.value === value)?.label ?? value
}

function analysisCategoryLabel(value: string) {
  if (!value) return ''
  return meta.value?.analysis_categories.find((c) => c.value === value)?.label ?? value
}

const needsSourcePriority = computed(
  () => form.rule === 'source_priority' || form.fallback_rule === 'source_priority',
)

onMounted(load)
</script>

<template>
  <div class="max-w-6xl mx-auto p-4 space-y-4">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-lg font-medium">Parameter consensus policies</h1>
        <p class="text-sm text-aots-muted mt-1">
          Choose which measurements are authoritative per parameter (e.g. Gaia DR3 parallax).
        </p>
      </div>
      <AppButton v-if="canEdit" variant="primary" size="sm" @click="openCreate">
        Add policy
      </AppButton>
    </header>

    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <p v-if="loading" class="text-sm text-aots-muted">Loading…</p>

    <section v-else class="aots-panel overflow-x-auto">
      <table class="aots-table w-full text-sm">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Component</th>
            <th>Rule</th>
            <th>Source / category</th>
            <th>Fallback</th>
            <th v-if="canEdit" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in policies" :key="row.id">
            <td>{{ parameterLabel(row.name) }}</td>
            <td>{{ componentLabel(row.component) }}</td>
            <td>{{ ruleLabel(row.rule) }}</td>
            <td>
              <span v-if="row.preferred_source_name">{{ row.preferred_source_name }}</span>
              <span v-else-if="row.preferred_analysis_category">
                {{ analysisCategoryLabel(row.preferred_analysis_category) }}
              </span>
              <span v-else-if="row.source_priority?.length">{{ row.source_priority.join(' → ') }}</span>
              <span v-else class="text-aots-muted">—</span>
            </td>
            <td>
              <span v-if="row.fallback_rule">{{ ruleLabel(row.fallback_rule) }}</span>
              <span v-if="row.fallback_preferred_source_name"> · {{ row.fallback_preferred_source_name }}</span>
              <span v-else-if="row.fallback_analysis_category">
                · {{ analysisCategoryLabel(row.fallback_analysis_category) }}
              </span>
              <span v-else-if="!row.fallback_rule" class="text-aots-muted">—</span>
            </td>
            <td v-if="canEdit" class="whitespace-nowrap">
              <div class="flex items-center gap-4">
                <AppButton variant="link" size="sm" @click="openEdit(row)">Edit</AppButton>
                <AppButton
                  v-if="row.name !== '*'"
                  variant="link"
                  size="sm"
                  class="text-red-400"
                  @click="deletePolicy(row)"
                >
                  Delete
                </AppButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!policies.length" class="p-4 text-sm text-aots-muted">No policies configured.</p>
    </section>

    <section v-if="editorOpen" class="aots-panel space-y-3">
      <h2 class="text-sm font-medium">{{ editingId ? 'Edit policy' : 'New policy' }}</h2>
      <div class="grid gap-3 md:grid-cols-2">
        <label class="block text-xs">
          <span class="text-aots-muted">Parameter</span>
          <select v-model="form.name" class="aots-field mt-1 w-full">
            <template
              v-for="(entry, idx) in meta?.parameter_choices ?? []"
              :key="`param-${idx}`"
            >
              <optgroup v-if="isChoiceGroup(entry)" :label="entry.group">
                <option
                  v-for="opt in entry.options"
                  :key="opt.value"
                  :value="opt.value"
                >
                  {{ opt.label }}
                </option>
              </optgroup>
              <option v-else :value="entry.value">
                {{ entry.label }}
              </option>
            </template>
          </select>
        </label>
        <label class="block text-xs">
          <span class="text-aots-muted">Component</span>
          <select v-model.number="form.component" class="aots-field mt-1 w-full">
            <option v-for="c in meta?.components ?? []" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </label>
        <label class="block text-xs">
          <span class="text-aots-muted">Rule</span>
          <select v-model="form.rule" class="aots-field mt-1 w-full">
            <option v-for="r in meta?.rules ?? []" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </label>
        <label v-if="form.rule === 'preferred_source'" class="block text-xs">
          <span class="text-aots-muted">Preferred source</span>
          <select v-model="form.preferred_source" class="aots-field mt-1 w-full">
            <option :value="null">—</option>
            <option v-for="s in meta?.sources ?? []" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </label>
        <label v-if="form.rule === 'preferred_analysis_category'" class="block text-xs">
          <span class="text-aots-muted">Analysis category</span>
          <select v-model="form.preferred_analysis_category" class="aots-field mt-1 w-full">
            <option value="">—</option>
            <option v-for="c in meta?.analysis_categories ?? []" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </label>
        <label class="block text-xs">
          <span class="text-aots-muted">Fallback rule</span>
          <select v-model="form.fallback_rule" class="aots-field mt-1 w-full">
            <option value="">—</option>
            <option v-for="r in meta?.rules ?? []" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </label>
        <label v-if="form.fallback_rule === 'preferred_source'" class="block text-xs">
          <span class="text-aots-muted">Fallback source</span>
          <select v-model="form.fallback_preferred_source" class="aots-field mt-1 w-full">
            <option :value="null">—</option>
            <option v-for="s in meta?.sources ?? []" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </label>
        <label v-if="form.fallback_rule === 'preferred_analysis_category'" class="block text-xs">
          <span class="text-aots-muted">Fallback category</span>
          <select v-model="form.fallback_analysis_category" class="aots-field mt-1 w-full">
            <option value="">—</option>
            <option v-for="c in meta?.analysis_categories ?? []" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </label>
        <label v-if="needsSourcePriority" class="block text-xs md:col-span-2">
          <span class="text-aots-muted">Source priority (comma-separated names or IDs)</span>
          <input v-model="form.source_priority" class="aots-field mt-1 w-full" />
        </label>
      </div>
      <div class="flex gap-2">
        <AppButton variant="primary" size="sm" :disabled="saving" @click="savePolicy">Save</AppButton>
        <AppButton variant="ghost" size="sm" @click="editorOpen = false">Cancel</AppButton>
      </div>
    </section>
  </div>
</template>
