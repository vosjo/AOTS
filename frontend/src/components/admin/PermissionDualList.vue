<script setup lang="ts">
import { computed, ref, watch } from 'vue'

export interface PermissionOption {
  id: number
  codename: string
  name: string
  app_label: string
  model: string
}

const props = defineProps<{
  permissions: PermissionOption[]
  modelValue: number[]
}>()

const emit = defineEmits<{
  'update:modelValue': [number[]]
}>()

const chosenIds = computed(() => new Set(props.modelValue))

const availableFilter = ref('')
const chosenFilter = ref('')
const availableSelection = ref<number[]>([])
const chosenSelection = ref<number[]>([])

function formatLabel(perm: PermissionOption): string {
  return `${perm.app_label} | ${perm.model} | ${perm.name}`
}

function matchesFilter(perm: PermissionOption, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  return (
    perm.app_label.toLowerCase().includes(q)
    || perm.model.toLowerCase().includes(q)
    || perm.codename.toLowerCase().includes(q)
    || perm.name.toLowerCase().includes(q)
  )
}

const availablePermissions = computed(() =>
  props.permissions
    .filter((p) => !chosenIds.value.has(p.id))
    .filter((p) => matchesFilter(p, availableFilter.value))
    .sort((a, b) => formatLabel(a).localeCompare(formatLabel(b))),
)

const chosenPermissions = computed(() =>
  props.permissions
    .filter((p) => chosenIds.value.has(p.id))
    .filter((p) => matchesFilter(p, chosenFilter.value))
    .sort((a, b) => formatLabel(a).localeCompare(formatLabel(b))),
)

function setChosen(ids: number[]) {
  emit('update:modelValue', ids)
}

function addIds(ids: number[]) {
  if (!ids.length) return
  const next = new Set(props.modelValue)
  for (const id of ids) next.add(id)
  setChosen([...next])
  availableSelection.value = []
}

function removeIds(ids: number[]) {
  if (!ids.length) return
  const remove = new Set(ids)
  setChosen(props.modelValue.filter((id) => !remove.has(id)))
  chosenSelection.value = []
}

function addSelected() {
  addIds(availableSelection.value)
}

function addAll() {
  addIds(availablePermissions.value.map((p) => p.id))
}

function removeSelected() {
  removeIds(chosenSelection.value)
}

function removeAll() {
  removeIds(chosenPermissions.value.map((p) => p.id))
}

function onAvailableDblClick(event: MouseEvent) {
  const option = event.target as HTMLOptionElement
  if (option?.value) addIds([Number(option.value)])
}

function onChosenDblClick(event: MouseEvent) {
  const option = event.target as HTMLOptionElement
  if (option?.value) removeIds([Number(option.value)])
}

watch(availableFilter, () => {
  availableSelection.value = []
})

watch(chosenFilter, () => {
  chosenSelection.value = []
})
</script>

<template>
  <div class="space-y-2">
    <p class="text-sm text-slate-300">
      {{ modelValue.length }} of {{ permissions.length }} permissions selected.
      Double-click a row to move it; use the arrows for bulk moves.
    </p>

    <div class="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]">
      <div class="space-y-2">
        <div class="flex items-center justify-between gap-2">
          <label class="text-sm font-medium text-slate-200">Available permissions</label>
          <button type="button" class="text-xs text-sky-400 hover:text-sky-300" @click="addAll">
            Choose all
          </button>
        </div>
        <input
          v-model="availableFilter"
          class="aots-field"
          placeholder="Filter available…"
          autocomplete="off"
        />
        <select
          v-model="availableSelection"
          multiple
          size="16"
          class="aots-dual-list"
          @dblclick="onAvailableDblClick"
        >
          <option v-for="perm in availablePermissions" :key="perm.id" :value="perm.id">
            {{ formatLabel(perm) }}
          </option>
        </select>
      </div>

      <div class="flex flex-row items-center justify-center gap-2 lg:flex-col lg:py-8">
        <button type="button" class="aots-btn-secondary px-3" title="Add selected" @click="addSelected">
          &gt;
        </button>
        <button type="button" class="aots-btn-secondary px-3" title="Add all filtered" @click="addAll">
          &gt;&gt;
        </button>
        <button type="button" class="aots-btn-secondary px-3" title="Remove selected" @click="removeSelected">
          &lt;
        </button>
        <button type="button" class="aots-btn-secondary px-3" title="Remove all filtered" @click="removeAll">
          &lt;&lt;
        </button>
      </div>

      <div class="space-y-2">
        <div class="flex items-center justify-between gap-2">
          <label class="text-sm font-medium text-slate-200">Chosen permissions</label>
          <button type="button" class="text-xs text-sky-400 hover:text-sky-300" @click="removeAll">
            Remove all
          </button>
        </div>
        <input
          v-model="chosenFilter"
          class="aots-field"
          placeholder="Filter chosen…"
          autocomplete="off"
        />
        <select
          v-model="chosenSelection"
          multiple
          size="16"
          class="aots-dual-list"
          @dblclick="onChosenDblClick"
        >
          <option v-for="perm in chosenPermissions" :key="perm.id" :value="perm.id">
            {{ formatLabel(perm) }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<style scoped>
.aots-dual-list {
  width: 100%;
  min-height: 18rem;
  border-radius: 0.375rem;
  border: 1px solid rgb(71 85 105);
  background: rgb(15 23 42);
  color: rgb(241 245 249);
  font-size: 0.8125rem;
  line-height: 1.35;
}

.aots-dual-list option {
  padding: 0.2rem 0.4rem;
}

.aots-dual-list option:checked {
  background: rgb(14 116 144);
  color: white;
}
</style>
