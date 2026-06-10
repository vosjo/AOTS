const STORAGE_KEY = 'aots_carryover_pks'

export function saveCarryOver(pks: number[]) {
  sessionStorage.setItem(STORAGE_KEY, pks.join(';'))
}

export function loadCarryOver(): number[] {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return []
  sessionStorage.removeItem(STORAGE_KEY)
  return raw.split(';').map(Number).filter(Boolean)
}

export function carryOverFilter(): Record<string, string> | undefined {
  const pks = loadCarryOver()
  if (!pks.length) return undefined
  return { pk: pks.join(',') }
}
