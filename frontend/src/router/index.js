import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    meta: { auth: true },
    children: [
      { path: '', redirect: '/tri' },
      // TRI module
      {
        path: 'tri',
        redirect: '/tri/courses',
        meta: { module: 'TRI' },
      },
      {
        path: 'tri/courses',
        name: 'tri-courses',
        component: () => import('../views/tri/TriDashboardView.vue'),
        meta: { module: 'TRI' },
      },
      {
        path: 'tri/overview',
        name: 'tri-overview',
        component: () => import('../views/tri/TriOverviewView.vue'),
        meta: { module: 'TRI' },
      },
      {
        path: 'tri/events/:id',
        name: 'tri-event',
        component: () => import('../views/tri/TriEventView.vue'),
        meta: { module: 'TRI' },
      },
      {
        path: 'tri/events/:id/photos',
        name: 'tri-photos',
        component: () => import('../views/tri/TriPhotosView.vue'),
        meta: { module: 'TRI' },
      },
      {
        path: 'tri/events/:id/tools',
        name: 'tri-tools',
        component: () => import('../views/tri/TriToolsView.vue'),
        meta: { module: 'TRI' },
      },
      {
        path: 'tri/training',
        name: 'tri-training',
        component: () => import('../views/tri/TrainingCenterView.vue'),
        meta: { module: 'TRI' },
      },
      // WEB module
      {
        path: 'web',
        redirect: '/web/courses',
        meta: { module: 'WEB' },
      },
      {
        path: 'web/courses',
        name: 'web-courses',
        component: () => import('../views/web/WebCoursesView.vue'),
        meta: { module: 'WEB' },
      },
      {
        path: 'web/ecommerce',
        name: 'web-ecommerce',
        component: () => import('../views/web/WebEcommerceView.vue'),
        meta: { module: 'WEB' },
      },
      // MAILING module
      {
        path: 'mailing',
        name: 'mailing-dashboard',
        component: () => import('../views/mailing/MailingListView.vue'),
        meta: { module: 'MAILING' },
      },
      // SUPERADMIN
      {
        path: 'admin',
        name: 'admin-dashboard',
        component: () => import('../views/superadmin/SuperAdminView.vue'),
        meta: { role: 'SUPERADMIN' },
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: () => import('../views/superadmin/UserManagementView.vue'),
        meta: { role: 'SUPERADMIN' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Init auth on first load
  if (!auth.isLoggedIn && auth.token) {
    await auth.init()
  }

  // Guest-only pages
  if (to.meta.guest && auth.isLoggedIn) {
    return { path: '/' }
  }

  // Auth-required pages
  if (to.meta.auth && !auth.isLoggedIn) {
    return { path: '/login' }
  }

  // Check child route meta
  if (to.meta.module && !auth.hasModule(to.meta.module)) {
    return { path: '/' }
  }

  if (to.meta.role && auth.role !== to.meta.role) {
    return { path: '/' }
  }
})

export default router
