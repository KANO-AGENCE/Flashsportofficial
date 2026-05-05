import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/evenement/:slug',
    component: () => import('../views/EventView.vue'),
  },
  {
    path: '/evenement/:slug/dossard/:bib',
    component: () => import('../views/GalleryView.vue'),
  },
  {
    path: '/panier',
    component: () => import('../views/CartView.vue'),
  },
  {
    path: '/confirmation',
    component: () => import('../views/ConfirmationView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
