<script setup lang="ts">
import {
  ChartScatter,
  ChartSpline,
  FlaskConical,
  LayoutDashboard,
  Menu,
  Moon,
  Shield,
  Star,
  Sun,
  Telescope,
  User,
  type LucideIcon,
} from '@lucide/vue'
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppButton from '@/components/AppButton.vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const auth = useAuthStore()
const projectStore = useProjectStore()
const theme = useThemeStore()
const mobileOpen = ref(false)

const slug = computed(() => route.params.projectSlug as string | undefined)
const inProject = computed(() => !!slug.value)

const nav = computed(() => {
  if (!slug.value) return []
  const base = `/w/${slug.value}`
  const items: { to: string; label: string; icon: LucideIcon; activePrefix?: string }[] = [
    { to: `${base}/dash/`, label: 'Dashboard', icon: LayoutDashboard },
    { to: `${base}/systems/stars/`, label: 'Systems', icon: Star, activePrefix: `${base}/systems` },
    { to: `${base}/observations/spectra/`, label: 'Spectra', icon: ChartSpline, activePrefix: `${base}/observations/spectra` },
    { to: `${base}/observations/lightcurves/`, label: 'Light curves', icon: ChartScatter },
    { to: `${base}/observations/observatories/`, label: 'Observatories', icon: Telescope },
    { to: `${base}/analysis/analyses/`, label: 'Analyses', icon: FlaskConical, activePrefix: `${base}/analysis/analyses` },
  ]
  return items
})

function navActive(item: { to: string; activePrefix?: string }) {
  const prefix = item.activePrefix ?? item.to
  return route.path.startsWith(prefix)
}

async function logout() {
  await auth.logout()
  window.location.href = '/accounts/login/'
}
</script>

<template>
  <header class="aots-topbar">
    <div class="mx-auto flex h-14 max-w-[1600px] items-center gap-3 px-4">
      <RouterLink to="/w/projects/" class="shrink-0 font-semibold text-aots-brand hover:text-aots-link-hover">
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
          class="aots-topbar-nav-link"
          :class="{ 'aots-topbar-nav-link--active': navActive(item) }"
          :title="item.label"
        >
          <component :is="item.icon" class="h-4 w-4" />
          <span class="hidden xl:inline">{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="ml-auto flex items-center gap-2">
        <AppButton
          variant="icon"
          size="sm"
          class="!p-2"
          :title="theme.mode === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
          @click="theme.toggle()"
        >
          <Sun v-if="theme.mode === 'dark'" class="h-5 w-5" />
          <Moon v-else class="h-5 w-5" />
        </AppButton>
        <AppButton
          v-if="auth.isSuperuser"
          variant="ghost"
          size="sm"
          class="hidden sm:inline-flex items-center gap-1"
          to="/admin/"
          title="Administration"
        >
          <Shield class="h-4 w-4" />
          Admin
        </AppButton>
        <AppButton
          v-if="auth.isAuthenticated"
          variant="icon"
          class="!p-2"
          to="/users/you/"
          title="Profile"
        >
          <User class="h-5 w-5" />
        </AppButton>
        <AppButton v-else variant="primary" size="sm" to="/accounts/login/">Login</AppButton>
        <AppButton
          v-if="auth.isAuthenticated"
          variant="ghost"
          size="sm"
          @click="logout"
        >
          Logout
        </AppButton>
        <button
          type="button"
          class="aots-btn-icon !p-2 lg:hidden"
          @click="mobileOpen = !mobileOpen"
        >
          <Menu class="h-5 w-5" />
        </button>
      </div>
    </div>

    <nav v-if="mobileOpen && inProject" class="space-y-1 border-t border-aots px-4 py-2 lg:hidden">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="aots-topbar-nav-link text-sm"
        @click="mobileOpen = false"
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </RouterLink>
    </nav>
  </header>
</template>
