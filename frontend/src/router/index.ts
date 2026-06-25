import { createRouter, createWebHistory } from 'vue-router'
import { ensureCsrfToken } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

const routerBase =
  (typeof window !== 'undefined' && window.__AOTS_BOOTSTRAP__?.routerBase) || '/app/'

const router = createRouter({
  history: createWebHistory(routerBase),
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
      path: '/w/:projectSlug/systems/',
      redirect: (to) => `/w/${to.params.projectSlug}/systems/stars/`,
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
      path: '/w/:projectSlug/analysis/analyses/',
      name: 'analyses',
      component: () => import('@/views/AnalysisListView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/analysis/analyses/:id/',
      name: 'analysis-detail',
      component: () => import('@/views/AnalysisDetailView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/analysis/methods',
      redirect: (to) => `/w/${to.params.projectSlug}/analysis/analyses/`,
    },
    {
      path: '/w/:projectSlug/analysis/analyses/plotter',
      name: 'analysis-plotter',
      component: () => import('@/views/ParameterPlotterView.vue'),
      meta: { requiresProject: true },
    },
    {
      path: '/w/:projectSlug/analysis/plotter',
      redirect: (to) => `/w/${to.params.projectSlug}/analysis/analyses/plotter`,
    },
    {
      path: '/w/:projectSlug/settings/consensus/',
      name: 'project-consensus-settings',
      component: () => import('@/views/ProjectConsensusSettingsView.vue'),
      meta: { requiresProject: true, requiresAuth: true },
    },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresSuperuser: true },
      children: [
        { path: '', name: 'admin-home', component: () => import('@/views/admin/AdminHomeView.vue') },
        { path: 'users', name: 'admin-users', component: () => import('@/views/admin/AdminUserListView.vue') },
        { path: 'users/:id', name: 'admin-user-edit', component: () => import('@/views/admin/AdminUserFormView.vue') },
        { path: 'projects', name: 'admin-projects', component: () => import('@/views/admin/AdminProjectListView.vue') },
        { path: 'projects/:id', name: 'admin-project-edit', component: () => import('@/views/admin/AdminProjectFormView.vue') },
        { path: 'groups', name: 'admin-groups', component: () => import('@/views/admin/AdminGroupListView.vue') },
        { path: 'groups/:id', name: 'admin-group-edit', component: () => import('@/views/admin/AdminGroupFormView.vue') },
        { path: 'tokens', name: 'admin-tokens', component: () => import('@/views/admin/AdminTokenListView.vue') },
        { path: 'tasks', name: 'admin-tasks', component: () => import('@/views/admin/AdminTaskListView.vue') },
        { path: 'log', name: 'admin-log', component: () => import('@/views/admin/AdminLogListView.vue') },
      ],
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
  if (!auth.loaded) {
    try {
      await auth.fetchMe()
    } catch {
      auth.user = { authenticated: false }
      auth.loaded = true
    }
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }

  if (to.meta.requiresSuperuser && !auth.isSuperuser) {
    return { name: 'not-found' }
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
