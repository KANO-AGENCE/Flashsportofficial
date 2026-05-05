<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Dashboard Admin</h1>
    <p class="text-gray-500 mb-8">Vue globale de la plateforme</p>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Chiffre d'affaires</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">0 EUR</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Photos traitees</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.photos }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Courses</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.events }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Utilisateurs</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.users }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/client'

const stats = ref({ photos: 0, events: 0, users: 0 })

onMounted(async () => {
  try {
    const res = await api.get('/superadmin/stats')
    stats.value = res.data
  } catch {}
})
</script>
