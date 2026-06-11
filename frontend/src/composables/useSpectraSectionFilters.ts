import { ref, watch, type Ref } from 'vue'
import { carryOverFilter } from '@/composables/useCarryOver'

const STORAGE_KEY = 'aots_spectra_section_filters'

/** Map view-specific filter keys to a shared canonical key in session storage. */
const CANONICAL_KEYS: Record<string, string> = {
  systems: 'target',
  target: 'target',
  expo_min: 'exptime_min',
  exptime_min: 'exptime_min',
  expo_max: 'exptime_max',
  exptime_max: 'exptime_max',
}

function canonicalKey(key: string): string {
  return CANONICAL_KEYS[key] ?? key
}

function loadPersisted(): Record<string, string> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Record<string, string>
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function savePersisted(filters: Record<string, string>) {
  const merged = loadPersisted()
  for (const [key, value] of Object.entries(filters)) {
    const canon = canonicalKey(key)
    if (value === '' || value === undefined) delete merged[canon]
    else merged[canon] = value
  }
  if (Object.keys(merged).length) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(merged))
  else sessionStorage.removeItem(STORAGE_KEY)
}

function mapPersistedToView(
  persisted: Record<string, string>,
  defaultFields: Record<string, string>,
): Record<string, string> {
  const result = { ...defaultFields }
  for (const key of Object.keys(defaultFields)) {
    const canon = canonicalKey(key)
    if (persisted[canon] !== undefined) result[key] = persisted[canon]
    else if (persisted[key] !== undefined) result[key] = persisted[key]
  }
  return result
}

export function useSpectraSectionFilters<T extends Record<string, string>>(
  defaultFields: T,
  options?: { carryOver?: boolean },
) {
  const fieldKeys = Object.keys(defaultFields)
  const persisted = loadPersisted()
  const carryOver = options?.carryOver ? carryOverFilter() : undefined
  const initial = mapPersistedToView(persisted, {
    ...defaultFields,
    ...(carryOver ?? {}),
  })

  const filters = ref(initial) as Ref<Record<string, string>>

  watch(filters, (value) => savePersisted(value), { deep: true })

  function clearFilters() {
    const cleared: Record<string, string> = {}
    for (const key of fieldKeys) {
      filters.value[key] = ''
      cleared[key] = ''
    }
    savePersisted(cleared)
  }

  return { filters, clearFilters }
}
