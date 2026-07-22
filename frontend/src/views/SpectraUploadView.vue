<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
import { api, formatApiError } from '@/api/client'
import { useProjectPermissions } from '@/composables/useProjectPermissions'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import {
  parseUploadFeedback,
  type UploadFeedbackItem,
} from '@/utils/uploadFeedback'

interface ObservatoryOption {
  pk: number
  name: string
}

interface UploadForm {
  add_info: boolean
  filetype: string
  objectname: string
  ra: string
  dec: string
  create_new_star: boolean
  classification: string
  classification_type: string
  observer: string
  hjd: string
  telescope: string
  instrument: string
  exptime: string
  resolution: string
  snr: string
  wind_direction: string
  wind_speed: string
  seeing: string
  airmass: string
  normalized: boolean
  barycor_bool: boolean
  fluxcal: boolean
  flux_units: string
  master: boolean
  decomposed: boolean
  observatory: string
  observatory_name: string
  observatory_latitude: string
  observatory_longitude: string
  observatory_altitude: string
  observatory_is_spacecraft: boolean
  note: string
}

const emptyForm = (): UploadForm => ({
  add_info: false,
  filetype: '',
  objectname: '',
  ra: '',
  dec: '',
  create_new_star: true,
  classification: '',
  classification_type: 'PH',
  observer: '',
  hjd: '',
  telescope: '',
  instrument: '',
  exptime: '',
  resolution: '',
  snr: '',
  wind_direction: '',
  wind_speed: '',
  seeing: '',
  airmass: '',
  normalized: false,
  barycor_bool: true,
  fluxcal: false,
  flux_units: '',
  master: false,
  decomposed: false,
  observatory: '',
  observatory_name: '',
  observatory_latitude: '',
  observatory_longitude: '',
  observatory_altitude: '',
  observatory_is_spacecraft: false,
  note: '',
})

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const auth = useAuthStore()
const { canAdd } = useProjectPermissions()
const projectStore = useProjectStore()
const projectSlug = computed(() => route.params.projectSlug as string)

const files = ref<FileList | null>(null)
const form = ref<UploadForm>(emptyForm())
const uploadFeedback = ref<UploadFeedbackItem[]>([])
const uploading = ref(false)
const busy = ref(false)

const headerEnabled = computed(() => form.value.add_info)
const classificationEnabled = computed(() => form.value.add_info && form.value.create_new_star)
const newObservatory = computed(() => form.value.add_info && !form.value.observatory)
const observatoryCoordsEnabled = computed(
  () => newObservatory.value && !form.value.observatory_is_spacecraft,
)
const fluxUnitsEnabled = computed(() => form.value.add_info && form.value.fluxcal)
const normalizedEnabled = computed(() => form.value.add_info && !form.value.fluxcal)

const { data: observatories } = useQuery({
  queryKey: computed(() => ['observatories', projectStore.currentProject?.pk, 'upload']),
  queryFn: () =>
    api<{ results: ObservatoryOption[] }>(
      `/api/observations/observatories/?project=${projectStore.currentProject!.pk}&page_size=500`,
    ),
  enabled: computed(() => !!projectStore.currentProject),
})

watch(
  () => form.value.fluxcal,
  (fluxcal) => {
    if (fluxcal) form.value.normalized = false
  },
)

watch(
  () => form.value.normalized,
  (normalized) => {
    if (normalized) {
      form.value.fluxcal = false
      form.value.flux_units = ''
    }
  },
)

function onFilesChange(event: Event) {
  files.value = (event.target as HTMLInputElement).files
}

function appendTextField(fd: FormData, key: string, value: string) {
  if (value.trim()) fd.append(key, value.trim())
}

function appendBoolField(fd: FormData, key: string, value: boolean) {
  if (value) fd.append(key, 'on')
}

function appendHeaderFields(fd: FormData) {
  appendBoolField(fd, 'add_info', form.value.add_info)
  if (!form.value.add_info) return

  appendTextField(fd, 'filetype', form.value.filetype)
  appendTextField(fd, 'objectname', form.value.objectname)
  appendTextField(fd, 'ra', form.value.ra)
  appendTextField(fd, 'dec', form.value.dec)
  appendBoolField(fd, 'create_new_star', form.value.create_new_star)
  if (classificationEnabled.value) {
    appendTextField(fd, 'classification', form.value.classification)
    if (form.value.classification_type) fd.append('classification_type', form.value.classification_type)
  }
  appendTextField(fd, 'observer', form.value.observer)
  appendTextField(fd, 'hjd', form.value.hjd)
  appendTextField(fd, 'telescope', form.value.telescope)
  appendTextField(fd, 'instrument', form.value.instrument)
  appendTextField(fd, 'exptime', form.value.exptime)
  appendTextField(fd, 'resolution', form.value.resolution)
  appendTextField(fd, 'snr', form.value.snr)
  appendTextField(fd, 'wind_direction', form.value.wind_direction)
  appendTextField(fd, 'wind_speed', form.value.wind_speed)
  appendTextField(fd, 'seeing', form.value.seeing)
  appendTextField(fd, 'airmass', form.value.airmass)
  appendBoolField(fd, 'normalized', form.value.normalized)
  appendBoolField(fd, 'barycor_bool', form.value.barycor_bool)
  appendBoolField(fd, 'fluxcal', form.value.fluxcal)
  appendTextField(fd, 'flux_units', form.value.flux_units)
  appendBoolField(fd, 'master', form.value.master)
  appendBoolField(fd, 'decomposed', form.value.decomposed)
  if (form.value.observatory) {
    fd.append('observatory', form.value.observatory)
  } else if (newObservatory.value) {
    appendTextField(fd, 'observatory_name', form.value.observatory_name)
    appendBoolField(fd, 'observatory_is_spacecraft', form.value.observatory_is_spacecraft)
    if (observatoryCoordsEnabled.value) {
      appendTextField(fd, 'observatory_latitude', form.value.observatory_latitude)
      appendTextField(fd, 'observatory_longitude', form.value.observatory_longitude)
      appendTextField(fd, 'observatory_altitude', form.value.observatory_altitude)
    }
  }
  if (form.value.note.trim()) fd.append('note', form.value.note.trim())
}

async function upload() {
  if (!files.value?.length || !projectStore.currentProject) return
  busy.value = true
  uploading.value = true
  uploadFeedback.value = []
  const fd = new FormData()
  fd.append('project', String(projectStore.currentProject.pk))
  for (const f of files.value) fd.append('spectrumfile', f)
  appendHeaderFields(fd)

  try {
    const res = await api<{ detail?: string } | string>('/api/observations/api-spec-upload/', {
      method: 'POST',
      body: fd,
      headers: {
        Projectid: String(projectStore.currentProject.pk),
      },
    })
    const detail = typeof res === 'string' ? res : (res.detail ?? '')
    const feedback = parseUploadFeedback(detail)
    const allOk = !feedback.length || feedback.every((item) => item.kind === 'success')
    if (allOk) {
      await queryClient.invalidateQueries({ queryKey: ['/api/observations/spectra/'] })
      await queryClient.invalidateQueries({ queryKey: ['/api/observations/specfiles/'] })
      await router.push({
        path: `/w/${projectSlug.value}/observations/spectra/`,
        query: { uploaded: '1' },
      })
      return
    }
    uploadFeedback.value = feedback
  } catch (e) {
    uploadFeedback.value = parseUploadFeedback(formatApiError(e))
  } finally {
    busy.value = false
    uploading.value = false
  }
}
</script>

<template>
  <div class="space-y-6 max-w-6xl">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-2xl font-semibold">Spectra: Upload</h1>
      <AppButton variant="secondary" :to="`/w/${projectSlug}/observations/spectra/`">
        Back to list
      </AppButton>
    </div>

    <p v-if="!auth.isAuthenticated" class="aots-panel text-aots-muted">
      Log in to upload files.
    </p>

    <p v-else-if="!canAdd" class="aots-panel text-aots-muted">
      You do not have permission to upload spectra in this project.
    </p>

    <template v-else>
      <section class="aots-panel space-y-4">
        <div>
          <h2 class="font-medium">File selection</h2>
          <p class="text-sm text-aots-muted">(required)</p>
        </div>
        <label class="block">
          <span class="aots-label">File(s), .txt or .fits</span>
          <input
            type="file"
            multiple
            accept=".txt,.fits,.fit,.fz"
            class="aots-field w-full"
            @change="onFilesChange"
          />
        </label>
      </section>

      <section class="aots-panel space-y-4">
        <div>
          <h2 class="font-medium">Header information</h2>
          <p class="text-sm text-aots-muted">
            Underlined fields are required for .txt files or if they are not included in the header.
          </p>
        </div>

        <label class="flex items-center gap-2">
          <input v-model="form.add_info" type="checkbox" />
          <span>Add to / modify header data</span>
        </label>

        <div
          class="grid gap-6 lg:grid-cols-2 xl:grid-cols-3"
          :class="{ 'opacity-50': !headerEnabled }"
        >
          <div class="space-y-3">
            <h3 class="text-sm font-medium text-aots-muted">Target</h3>
            <label class="block">
              <span class="aots-label">Target <span v-if="headerEnabled" class="underline">*</span></span>
              <input v-model="form.objectname" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
            <label class="block">
              <span class="aots-label">RA <span v-if="headerEnabled" class="underline">*</span></span>
              <input
                v-model="form.ra"
                type="text"
                class="aots-field w-full"
                placeholder="h:m:s or d.d°"
                :disabled="!headerEnabled"
              />
            </label>
            <label class="block">
              <span class="aots-label">Dec <span v-if="headerEnabled" class="underline">*</span></span>
              <input
                v-model="form.dec"
                type="text"
                class="aots-field w-full"
                placeholder="° : ' : '' or d.d°"
                :disabled="!headerEnabled"
              />
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.create_new_star" type="checkbox" :disabled="!headerEnabled" />
              Create new
            </label>
            <label class="block">
              <span class="aots-label">Spectral classification</span>
              <input
                v-model="form.classification"
                type="text"
                class="aots-field w-full"
                :disabled="!classificationEnabled"
              />
            </label>
            <label class="block">
              <span class="aots-label">Classification type</span>
              <select
                v-model="form.classification_type"
                class="aots-select w-full"
                :disabled="!classificationEnabled"
              >
                <option value="PH">Photometric</option>
                <option value="SP">Spectroscopic</option>
              </select>
            </label>

            <h3 class="text-sm font-medium text-aots-muted pt-2">Observer</h3>
            <label class="block">
              <span class="aots-label">Observer name</span>
              <input v-model="form.observer" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
          </div>

          <div class="space-y-3">
            <h3 class="text-sm font-medium text-aots-muted">Instrument setup</h3>
            <label class="block">
              <span class="aots-label">HJD-MID <span v-if="headerEnabled" class="underline">*</span></span>
              <input v-model="form.hjd" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
            <label class="block">
              <span class="aots-label">Telescope</span>
              <input v-model="form.telescope" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
            <label class="block">
              <span class="aots-label">Instrument</span>
              <input v-model="form.instrument" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
            <label class="block">
              <span class="aots-label">Exptime (s)</span>
              <input v-model="form.exptime" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
            <label class="block">
              <span class="aots-label">Resolution</span>
              <input v-model="form.resolution" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
            <label class="block">
              <span class="aots-label">SNR</span>
              <input v-model="form.snr" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>

            <h3 class="text-sm font-medium text-aots-muted pt-2">Wind conditions</h3>
            <label class="block">
              <span class="aots-label">Wind direction (deg)</span>
              <input
                v-model="form.wind_direction"
                type="text"
                class="aots-field w-full"
                :disabled="!headerEnabled"
              />
            </label>
            <label class="block">
              <span class="aots-label">Wind speed (m/s)</span>
              <input v-model="form.wind_speed" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
          </div>

          <div class="space-y-3">
            <h3 class="text-sm font-medium text-aots-muted">Seeing and airmass</h3>
            <label class="block">
              <span class="aots-label">Seeing (&quot;)</span>
              <input v-model="form.seeing" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
            <label class="block">
              <span class="aots-label">Airmass</span>
              <input v-model="form.airmass" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>

            <h3 class="text-sm font-medium text-aots-muted pt-2">Spectrum processing</h3>
            <label class="flex items-center gap-2">
              <input v-model="form.barycor_bool" type="checkbox" :disabled="!headerEnabled" />
              Barycentric corrected
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.normalized" type="checkbox" :disabled="!normalizedEnabled" />
              Normalized
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.fluxcal" type="checkbox" :disabled="!headerEnabled" />
              Flux calibrated
            </label>
            <label class="block">
              <span class="aots-label">Flux units</span>
              <input
                v-model="form.flux_units"
                type="text"
                class="aots-field w-full"
                :disabled="!fluxUnitsEnabled"
              />
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.master" type="checkbox" :disabled="!headerEnabled" />
              Master spectrum
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.decomposed" type="checkbox" :disabled="!headerEnabled" />
              Master decomposed
            </label>
            <label class="block">
              <span class="aots-label">File label</span>
              <input v-model="form.filetype" type="text" class="aots-field w-full" :disabled="!headerEnabled" />
            </label>
          </div>

          <div class="space-y-3 lg:col-span-2 xl:col-span-1">
            <h3 class="text-sm font-medium text-aots-muted">Observatory</h3>
            <label class="block">
              <span class="aots-label">Observatory</span>
              <select v-model="form.observatory" class="aots-select w-full" :disabled="!headerEnabled">
                <option value="">— new observatory —</option>
                <option
                  v-for="obs in observatories?.results ?? []"
                  :key="obs.pk"
                  :value="String(obs.pk)"
                >
                  {{ obs.name }}
                </option>
              </select>
            </label>

            <template v-if="newObservatory">
              <label class="block">
                <span class="aots-label">
                  Name <span class="underline">*</span>
                </span>
                <input
                  v-model="form.observatory_name"
                  type="text"
                  class="aots-field w-full"
                  :disabled="!headerEnabled"
                />
              </label>
              <label class="flex items-center gap-2">
                <input
                  v-model="form.observatory_is_spacecraft"
                  type="checkbox"
                  :disabled="!headerEnabled"
                />
                Is spacecraft
              </label>
              <label class="block">
                <span class="aots-label">
                  Latitude (deg) <span v-if="observatoryCoordsEnabled" class="underline">*</span>
                </span>
                <input
                  v-model="form.observatory_latitude"
                  type="text"
                  class="aots-field w-full"
                  :disabled="!observatoryCoordsEnabled"
                />
              </label>
              <label class="block">
                <span class="aots-label">
                  Longitude (deg) <span v-if="observatoryCoordsEnabled" class="underline">*</span>
                </span>
                <input
                  v-model="form.observatory_longitude"
                  type="text"
                  class="aots-field w-full"
                  :disabled="!observatoryCoordsEnabled"
                />
              </label>
              <label class="block">
                <span class="aots-label">
                  Altitude (m) <span v-if="observatoryCoordsEnabled" class="underline">*</span>
                </span>
                <input
                  v-model="form.observatory_altitude"
                  type="text"
                  class="aots-field w-full"
                  :disabled="!observatoryCoordsEnabled"
                />
              </label>
            </template>

            <h3 class="text-sm font-medium text-aots-muted pt-2">Note</h3>
            <textarea
              v-model="form.note"
              rows="6"
              class="aots-field w-full"
              :disabled="!headerEnabled"
            />
          </div>
        </div>
      </section>

      <div class="space-y-4">
        <AppButton
          variant="primary"
          :disabled="busy || !files?.length"
          @click="upload"
        >
          Upload
        </AppButton>

        <p v-if="uploading" class="text-sm text-aots-muted">Uploading and processing files…</p>

        <div v-if="uploadFeedback.length" class="space-y-3">
          <AppAlert
            v-for="(item, index) in uploadFeedback"
            :key="index"
            :kind="item.kind"
            :title="item.title"
          >
            <p v-if="item.filename" class="font-mono text-xs break-all opacity-90">
              {{ item.filename }}
            </p>
            <p v-if="item.detail" class="leading-relaxed opacity-90">
              {{ item.detail }}
            </p>
          </AppAlert>
        </div>
      </div>
    </template>
  </div>
</template>
