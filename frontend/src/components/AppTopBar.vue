<script setup lang="ts">
import {
  BarChart3,
  Binoculars,
  FlaskConical,
  LayoutDashboard,
  Menu,
  Star,
  User,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useClassicToggle } from '@/composables/useClassicToggle'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const auth = useAuthStore()
const projectStore = useProjectStore()
const { toClassic } = useClassicToggle()
const mobileOpen = ref(false)

const slug = computed(() => route.params.projectSlug as string | undefined)
const inProject = computed(() => !!slug.value)

const nav = computed(() => {
  if (!slug.value) return []
  const base = `/w/${slug.value}`
  return [
    { to: `${base}/dash/`, label: 'Dashboard', icon: LayoutDashboard },
    { to: `${base}/systems/stars/`, label: 'Stars', icon: Star },
    { to: `${base}/systems/tags/`, label: 'Tags', icon: Star },
    { to: `${base}/observations/spectra/`, label: 'Spectra', icon: Binoculars },
    { to: `${base}/observations/specfiles/`, label: 'Specfiles', icon: Binoculars },
    { to: `${base}/observations/rawspecfiles/`, label: 'Raw', icon: Binoculars },
    { to: `${base}/observations/lightcurves/`, label: 'Light curves', icon: Binoculars },
    { to: `${base}/observations/observatories/`, label: 'Observatories', icon: Binoculars },
    { to: `${base}/analysis/datasets/`, label: 'Datasets', icon: FlaskConical },
    { to: `${base}/analysis/methods`, label: 'Methods', icon: FlaskConical },
    { to: `${base}/analysis/plotter`, label: 'Plotter', icon: BarChart3 },
  ]
})

async function logout() {
  await auth.logout()
  window.location.href = '/accounts/login/'
}
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-slate-600 bg-slate-900/95 backdrop-blur">
    <div class="mx-auto flex h-14 max-w-[1600px] items-center gap-3 px-4">
      <RouterLink to="/w/projects/" class="shrink-0 font-semibold text-sky-300 hover:text-sky-200">
        AOTS
      </RouterLink>

      <select
        v-if="projectStore.projects.length"
        class="aots-select hidden max-w-[200px] truncate md:block"
        :value="slug || ''"
        @change="(e) => $router.push(`/w/${(e.target as HTMLSelectElement).value}/dash/`)"
      >
        <option value="" disabled>Project…</option>
        <option v-for="p in projectStore.projects" :key="p.slug" :value="p.slug">{{ p.name }}</option>
      </select>

      <nav v-if="inProject" class="hidden flex-1 items-center gap-1 overflow-x-auto lg:flex">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white"
          :class="{ 'bg-slate-700 text-white ring-1 ring-slate-500': route.path.startsWith(item.to) }"
          :title="item.label"
        >
          <component :is="item.icon" class="h-4 w-4" />
          <span class="hidden xl:inline">{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="ml-auto flex items-center gap-2">
        <a :href="toClassic()" class="aots-btn-secondary text-xs">Classic UI</a>
        <RouterLink
          v-if="auth.isAuthenticated"
          to="/users/you/"
          class="rounded-md p-2 text-slate-200 hover:bg-slate-700 hover:text-white"
          title="Profile"
        >
          <User class="h-5 w-5" />
        </RouterLink>
        <RouterLink v-else to="/accounts/login/" class="aots-btn-primary text-xs">Login</RouterLink>
        <button
          v-if="auth.isAuthenticated"
          type="button"
          class="aots-btn-ghost text-xs"
          @click="logout"
        >
          Logout
        </button>
        <button type="button" class="rounded-md p-2 text-slate-200 hover:bg-slate-700 lg:hidden" @click="mobileOpen = !mobileOpen">
          <Menu class="h-5 w-5" />
        </button>
      </div>
    </div>

    <nav v-if="mobileOpen && inProject" class="space-y-1 border-t border-slate-600 px-4 py-2 lg:hidden">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-2 rounded-md px-2 py-2 text-sm font-medium text-slate-100 hover:bg-slate-700"
        @click="mobileOpen = false"
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </RouterLink>
    </nav>
  </header>
</template>
