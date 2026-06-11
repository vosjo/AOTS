import { createRouter, createWebHistory } from 'vue-router'
import { ensureCsrfToken } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

const router = createRouter({
  history: createWebHistory('/app/'),
  routes: [
    { path: '/', redirect: '/w/projects/' },
    {
      path: '/w/projects/',
      name: 'projects',
      component: () => import('@/views/ProjectListView.vue'),
    },
    {
      path: '/w/documentation/',
      name: 'documentation',
      component: () => import('@/views/DocumentationView.vue'),
    },
    {
      path: '/accounts/login/',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/accounts/password_change/',
      name: 'password-change',
      component: () => import('@/views/PasswordChangeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/users/you/',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/users/user/:id',
      name: 'user-profile',
      component: () => import('@/views/UserProfileView.vue'),
    },
    {
      path: '/w/:projectSlug',
      redirect: (to) => `/w/${to.params.projectSlug}/dash/`,
    },
    {
      path: '/w/:projectSlug/dash/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/systems/stars/',
      name: 'stars',
      component: () => import('@/views/StarListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/systems/stars/:id',
      name: 'star-detail',
      component: () => import('@/views/StarDetailView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/systems/stars/:id/edit',
      name: 'star-edit',
      component: () => import('@/views/StarEditView.vue'),
      meta: { requiresProject: true, requiresAuth: true },
    },
    {
      path: '/w/:projectSlug/systems/tags/',
      name: 'tags',
      component: () => import('@/views/TagListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/observations/spectra/raw/',
      name: 'spectra-raw',
      component: () => import('@/views/RawspecfileListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/observations/spectra/files/',
      name: 'spectra-files',
      component: () => import('@/views/SpecfileListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/observations/spectra/',
      name: 'spectra',
      component: () => import('@/views/SpectraListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/observations/spectra/upload',
      name: 'spectra-upload',
      component: () => import('@/views/SpectraUploadView.vue'),
      meta: { requiresProject: true, requiresAuth: true },
    },
    {
      path: '/w/:projectSlug/observations/spectra/:id/',
      name: 'spectrum-detail',
      component: () => import('@/views/SpectrumDetailView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/observations/specfiles/',
      redirect: (to) => `/w/${to.params.projectSlug}/observations/spectra/files/`,
    },
    {
      path: '/w/:projectSlug/observations/rawspecfiles/',
      redirect: (to) => `/w/${to.params.projectSlug}/observations/spectra/raw/`,
    },
    {
      path: '/w/:projectSlug/observations/lightcurves/',
      name: 'lightcurves',
      component: () => import('@/views/LightcurveListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/observations/lightcurves/:id/',
      name: 'lightcurve-detail',
      component: () => import('@/views/LightcurveDetailView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/observations/observatories/',
      name: 'observatories',
      component: () => import('@/views/ObservatoryListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/analysis/datasets/',
      name: 'datasets',
      component: () => import('@/views/DatasetListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/analysis/datasets/:id/',
      name: 'dataset-detail',
      component: () => import('@/views/DatasetDetailView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/analysis/methods',
      redirect: (to) => `/w/${to.params.projectSlug}/analysis/datasets/`,
    },
    {
      path: '/w/:projectSlug/analysis/plotter',
      name: 'plotter',
      component: () => import('@/views/ParameterPlotterView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  await ensureCsrfToken()
  const auth = useAuthStore()
  if (!auth.loaded) await auth.fetchMe()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }

  if (to.meta.requiresProject && to.params.projectSlug) {
    const projectStore = useProjectStore()
    if (!projectStore.projects.length) await projectStore.fetchProjects()
    const slug = String(to.params.projectSlug)
    const exists = projectStore.projects.some((p) => p.slug === slug)
    if (!exists) return { name: 'not-found' }
    await projectStore.setCurrentSlug(slug)
  }
})

export default router
