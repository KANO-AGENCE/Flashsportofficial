import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('fs_token') || null)

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const role = computed(() => user.value?.role || '')
  const modules = computed(() => user.value?.modules || [])
  const isSuperAdmin = computed(() => role.value === 'SUPERADMIN')
  const hasModule = (mod) => isSuperAdmin.value || modules.value.includes(mod)

  async function login(email, password) {
    const res = await authApi.login(email, password)
    token.value = res.data.access_token
    localStorage.setItem('fs_token', token.value)
    await fetchUser()
  }

  async function fetchUser() {
    try {
      const res = await authApi.me()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('fs_token')
  }

  async function init() {
    if (token.value) {
      await fetchUser()
    }
  }

  return { user, token, isLoggedIn, role, modules, isSuperAdmin, hasModule, login, fetchUser, logout, init }
})
