import { onUnmounted, ref, watch, type Ref } from 'vue'
import { api } from '@/api/client'

export interface SimbadMatch {
  main_id: string
  ra: string
  dec: string
  classification: string
  classification_type: string
}

interface SimbadResolveResult extends Partial<SimbadMatch> {
  status: 'unique' | 'ambiguous' | 'not_found' | 'empty'
  matches?: SimbadMatch[]
  best_match?: boolean
}

export interface SimbadResolvableForm {
  name: string
  ra: string
  dec: string
  classification: string
  classification_type: string
  get_simbad: boolean
}

export function useSimbadResolve(form: Ref<SimbadResolvableForm>) {
  const simbadResolving = ref(false)
  const simbadMessage = ref('')
  const simbadAmbiguous = ref<SimbadMatch[]>([])
  let simbadResolveTimer: ReturnType<typeof setTimeout> | undefined
  let resolveGeneration = 0

  function resetSimbadResolveState() {
    simbadMessage.value = ''
    simbadAmbiguous.value = []
    simbadResolving.value = false
    clearTimeout(simbadResolveTimer)
    resolveGeneration += 1
  }

  function applySimbadMatch(match: SimbadMatch) {
    form.value.ra = match.ra
    form.value.dec = match.dec
    form.value.classification = match.classification
    form.value.classification_type = match.classification_type
    simbadAmbiguous.value = []
  }

  function selectSimbadMatch(match: SimbadMatch) {
    form.value.name = match.main_id
    applySimbadMatch(match)
    simbadMessage.value = `Resolved: ${match.main_id}`
  }

  async function resolveSimbadName() {
    const name = form.value.name.trim()
    if (!name || !form.value.get_simbad) return

    const generation = ++resolveGeneration
    simbadResolving.value = true
    simbadMessage.value = ''
    simbadAmbiguous.value = []
    try {
      const res = await api<SimbadResolveResult>(
        `/api/systems/stars/resolve-simbad/?name=${encodeURIComponent(name)}`,
      )
      if (generation !== resolveGeneration) return
      if (res.status === 'unique' && res.main_id && res.ra && res.dec) {
        applySimbadMatch(res as SimbadMatch)
        simbadMessage.value = res.best_match
          ? `Resolved (best match): ${res.main_id}`
          : `Resolved: ${res.main_id}`
      } else if (res.status === 'ambiguous' && res.matches?.length) {
        simbadAmbiguous.value = res.matches
        simbadMessage.value = 'Multiple Simbad matches — please select one:'
        form.value.ra = ''
        form.value.dec = ''
        form.value.classification = ''
      } else {
        simbadMessage.value = 'No unique Simbad match found.'
        form.value.ra = ''
        form.value.dec = ''
        form.value.classification = ''
      }
    } catch (e) {
      if (generation !== resolveGeneration) return
      simbadMessage.value = e instanceof Error ? e.message : 'Simbad lookup failed'
    } finally {
      if (generation === resolveGeneration) {
        simbadResolving.value = false
      }
    }
  }

  function scheduleSimbadResolve() {
    clearTimeout(simbadResolveTimer)
    if (!form.value.get_simbad) return
    simbadResolveTimer = setTimeout(resolveSimbadName, 600)
  }

  watch(
    () => form.value.get_simbad,
    (useSimbad) => {
      if (!useSimbad) {
        resetSimbadResolveState()
        return
      }
      scheduleSimbadResolve()
    },
  )

  watch(
    () => form.value.name,
    () => {
      if (!form.value.get_simbad) return
      scheduleSimbadResolve()
    },
  )

  onUnmounted(() => {
    clearTimeout(simbadResolveTimer)
    resolveGeneration += 1
  })

  return {
    simbadResolving,
    simbadMessage,
    simbadAmbiguous,
    resetSimbadResolveState,
    selectSimbadMatch,
    resolveSimbadName,
  }
}
