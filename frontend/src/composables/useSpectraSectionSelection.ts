import { computed, ref, type Ref } from 'vue'

const STORAGE_KEY = 'aots_spectra_section_selection'

export type SpectraSectionKind = 'spectra' | 'specfiles' | 'rawspecfiles'

interface SelectionState {
  spectra: number[]
  specfiles: number[]
  rawspecfiles: number[]
  specfileToSpectrum: Record<string, number>
  rawLinks: Record<string, number[]>
}

interface SpectrumRow {
  pk: number
  specfiles?: { pk: number }[]
}

interface SpecfileRow {
  pk: number
  spectrum_info?: { pk: number } | null
  rawspecfiles?: number[]
}

interface RawspecfileRow {
  pk: number
  specfile?: number[]
  spectra?: number[]
}

function emptyState(): SelectionState {
  return {
    spectra: [],
    specfiles: [],
    rawspecfiles: [],
    specfileToSpectrum: {},
    rawLinks: {},
  }
}

function loadState(): SelectionState {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return emptyState()
    const parsed = JSON.parse(raw) as SelectionState
    return {
      ...emptyState(),
      ...parsed,
      specfileToSpectrum: parsed.specfileToSpectrum ?? {},
      rawLinks: parsed.rawLinks ?? {},
    }
  } catch {
    return emptyState()
  }
}

function persist(state: SelectionState) {
  const hasAny =
    state.spectra.length ||
    state.specfiles.length ||
    state.rawspecfiles.length
  if (hasAny) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  else sessionStorage.removeItem(STORAGE_KEY)
}

const state: Ref<SelectionState> = ref(loadState())
const revision = ref(0)

function bump() {
  revision.value += 1
  persist(state.value)
}

function asSet(values: number[]): Set<number> {
  return new Set(values)
}

function setToArray(set: Set<number>): number[] {
  return [...set]
}

function spectrumIdForSpecfile(specfilePk: number): number | undefined {
  return state.value.specfileToSpectrum[String(specfilePk)]
}

function spectrumStillSelected(spectrumPk: number): boolean {
  return Object.entries(state.value.specfileToSpectrum).some(
    ([specfilePk, spectrumId]) =>
      spectrumId === spectrumPk && state.value.specfiles.includes(Number(specfilePk)),
  )
}

function removeRawsWithoutSpecfileLink() {
  const linked = new Set(state.value.rawspecfiles)
  for (const rawPk of [...linked]) {
    const specfiles = state.value.rawLinks[String(rawPk)] ?? []
    if (!specfiles.some((sf) => state.value.specfiles.includes(sf))) {
      const idx = state.value.rawspecfiles.indexOf(rawPk)
      if (idx >= 0) state.value.rawspecfiles.splice(idx, 1)
    }
  }
}

function registerSpecfileSpectrum(specfilePk: number, spectrumPk: number) {
  state.value.specfileToSpectrum[String(specfilePk)] = spectrumPk
}

function registerRawLinks(rawPk: number, specfilePks: number[]) {
  state.value.rawLinks[String(rawPk)] = specfilePks
}

function linkSpectrumRow(row: SpectrumRow, on: boolean) {
  const spectra = new Set(state.value.spectra)
  const specfiles = new Set(state.value.specfiles)

  if (on) {
    spectra.add(row.pk)
    for (const sf of row.specfiles ?? []) {
      specfiles.add(sf.pk)
      registerSpecfileSpectrum(sf.pk, row.pk)
    }
  } else {
    spectra.delete(row.pk)
    for (const sf of row.specfiles ?? []) {
      specfiles.delete(sf.pk)
      delete state.value.specfileToSpectrum[String(sf.pk)]
    }
    removeRawsWithoutSpecfileLink()
  }

  state.value.spectra = setToArray(spectra)
  state.value.specfiles = setToArray(specfiles)
}

function linkSpecfileRow(row: SpecfileRow, on: boolean) {
  const specfiles = new Set(state.value.specfiles)
  const spectra = new Set(state.value.spectra)
  const raws = new Set(state.value.rawspecfiles)

  if (on) {
    specfiles.add(row.pk)
    if (row.spectrum_info?.pk) {
      spectra.add(row.spectrum_info.pk)
      registerSpecfileSpectrum(row.pk, row.spectrum_info.pk)
    }
    for (const rawPk of row.rawspecfiles ?? []) raws.add(rawPk)
  } else {
    specfiles.delete(row.pk)
    delete state.value.specfileToSpectrum[String(row.pk)]
    if (row.spectrum_info?.pk && !spectrumStillSelected(row.spectrum_info.pk)) {
      spectra.delete(row.spectrum_info.pk)
    }
    for (const rawPk of row.rawspecfiles ?? []) {
      const links = state.value.rawLinks[String(rawPk)] ?? [row.pk]
      if (!links.some((sf) => specfiles.has(sf))) raws.delete(rawPk)
    }
    removeRawsWithoutSpecfileLink()
  }

  state.value.specfiles = setToArray(specfiles)
  state.value.spectra = setToArray(spectra)
  state.value.rawspecfiles = setToArray(raws)
}

function linkRawspecfileRow(row: RawspecfileRow, on: boolean) {
  const raws = new Set(state.value.rawspecfiles)
  const specfiles = new Set(state.value.specfiles)
  const spectra = new Set(state.value.spectra)
  const specfilePks = row.specfile ?? []

  registerRawLinks(row.pk, specfilePks)

  if (on) {
    raws.add(row.pk)
    for (const sf of specfilePks) specfiles.add(sf)
    for (const spectrumPk of row.spectra ?? []) spectra.add(spectrumPk)
    for (const sf of specfilePks) {
      const spectrumPk = spectrumIdForSpecfile(sf)
      if (spectrumPk) spectra.add(spectrumPk)
    }
  } else {
    raws.delete(row.pk)
    for (const sf of specfilePks) {
      const stillLinked = [...raws].some((rawPk) =>
        (state.value.rawLinks[String(rawPk)] ?? []).includes(sf),
      )
      if (!stillLinked) {
        specfiles.delete(sf)
        const spectrumPk = spectrumIdForSpecfile(sf)
        delete state.value.specfileToSpectrum[String(sf)]
        if (spectrumPk && !spectrumStillSelected(spectrumPk)) spectra.delete(spectrumPk)
      }
    }
    removeRawsWithoutSpecfileLink()
  }

  state.value.rawspecfiles = setToArray(raws)
  state.value.specfiles = setToArray(specfiles)
  state.value.spectra = setToArray(spectra)
}

function syncRawsFromSpecfiles(rows: RawspecfileRow[]) {
  const raws = new Set(state.value.rawspecfiles)
  for (const row of rows) {
    registerRawLinks(row.pk, row.specfile ?? [])
    if ((row.specfile ?? []).some((sf) => state.value.specfiles.includes(sf))) {
      raws.add(row.pk)
    }
  }
  state.value.rawspecfiles = setToArray(raws)
}

export function useSpectraSectionSelection() {
  function getSelectedSet(kind: SpectraSectionKind): Set<number> {
    revision.value
    switch (kind) {
      case 'spectra':
        return asSet(state.value.spectra)
      case 'specfiles':
        return asSet(state.value.specfiles)
      case 'rawspecfiles':
        return asSet(state.value.rawspecfiles)
    }
  }

  const selectedSpectra = computed(() => getSelectedSet('spectra'))
  const selectedSpecfiles = computed(() => getSelectedSet('specfiles'))
  const selectedRawspecfiles = computed(() => getSelectedSet('rawspecfiles'))

  function isSelected(kind: SpectraSectionKind, pk: number): boolean {
    return getSelectedSet(kind).has(pk)
  }

  function toggle(kind: SpectraSectionKind, pk: number, row?: unknown) {
    const on = !isSelected(kind, pk)
    if (kind === 'spectra') linkSpectrumRow((row as SpectrumRow) ?? { pk }, on)
    else if (kind === 'specfiles') linkSpecfileRow((row as SpecfileRow) ?? { pk }, on)
    else linkRawspecfileRow((row as RawspecfileRow) ?? { pk }, on)
    bump()
  }

  function toggleAll(kind: SpectraSectionKind, rows: unknown[], forceOn?: boolean) {
    const allSelected = rows.length > 0 && rows.every((row) => isSelected(kind, (row as { pk: number }).pk))
    const on = forceOn ?? !allSelected
    for (const row of rows) {
      const pk = (row as { pk: number }).pk
      if (on === isSelected(kind, pk)) continue
      if (kind === 'spectra') linkSpectrumRow(row as SpectrumRow, on)
      else if (kind === 'specfiles') linkSpecfileRow(row as SpecfileRow, on)
      else linkRawspecfileRow(row as RawspecfileRow, on)
    }
    bump()
  }

  function indexRows(kind: SpectraSectionKind, rows: unknown[]) {
    for (const row of rows) {
      if (kind === 'spectra') {
        const spectrum = row as SpectrumRow
        for (const sf of spectrum.specfiles ?? []) registerSpecfileSpectrum(sf.pk, spectrum.pk)
      } else if (kind === 'specfiles') {
        const specfile = row as SpecfileRow
        if (specfile.spectrum_info?.pk) registerSpecfileSpectrum(specfile.pk, specfile.spectrum_info.pk)
      } else {
        registerRawLinks((row as RawspecfileRow).pk, (row as RawspecfileRow).specfile ?? [])
      }
    }
    if (kind === 'rawspecfiles') syncRawsFromSpecfiles(rows as RawspecfileRow[])
    bump()
  }

  function clearAll() {
    state.value = emptyState()
    bump()
  }

  return {
    selectedSpectra,
    selectedSpecfiles,
    selectedRawspecfiles,
    getSelectedSet,
    isSelected,
    toggle,
    toggleAll,
    indexRows,
    clearAll,
  }
}
