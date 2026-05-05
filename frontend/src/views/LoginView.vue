<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
    <div class="w-full max-w-md px-6">
      <!-- Logo -->
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-white tracking-tight">
          <span class="text-blue-400">Flash</span>Sport
        </h1>
        <p class="text-slate-400 mt-2">Plateforme de photographie sportive</p>
      </div>

      <!-- Login card -->
      <div class="bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl shadow-black/30 rounded-3xl p-8">
        <h2 class="text-xl font-semibold text-white mb-6">Connexion</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Email</label>
            <input
              v-model="email"
              type="email"
              required
              class="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400/60 outline-none transition backdrop-blur-sm"
              placeholder="admin@flashsport.fr"
            >
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Mot de passe</label>
            <input
              v-model="password"
              type="password"
              required
              class="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500/40 focus:border-blue-400/60 outline-none transition backdrop-blur-sm"
              placeholder="••••••••"
            >
          </div>

          <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 px-4 rounded-xl shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all disabled:opacity-50"
          >
            {{ loading ? 'Connexion...' : 'Se connecter' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Erreur de connexion'
  } finally {
    loading.value = false
  }
}
</script>
