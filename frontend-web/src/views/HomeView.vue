<template>
  <!-- Hero Section -->
  <section class="relative bg-gradient-to-br from-[var(--navy)] via-[var(--slate)] to-[var(--navy)] text-white overflow-hidden">
    <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSA2MCAwIEwgMCAwIDAgNjAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-50"></div>
    <div class="relative max-w-5xl mx-auto px-4 py-20 sm:py-28 text-center">
      <h1 class="font-display text-4xl sm:text-5xl lg:text-6xl font-bold mb-4 leading-tight">
        Trouvez vos photos<br>
        <span class="text-[var(--turquoise)]">en quelques secondes</span>
      </h1>
      <p class="text-lg text-white/70 mb-10 max-w-2xl mx-auto">
        Vous avez participe a un evenement sportif ? Retrouvez et telechargez vos photos en haute definition.
      </p>

      <!-- Search Bar -->
      <div class="bg-white rounded-2xl shadow-2xl p-2 max-w-2xl mx-auto flex flex-col sm:flex-row gap-2">
        <div class="flex-1 relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Nom de l'evenement..."
            class="w-full pl-10 pr-4 py-3 rounded-xl text-[var(--navy)] placeholder-gray-400 focus:outline-none text-sm"
            @input="filterEvents"
          >
        </div>
        <button class="bg-[var(--turquoise)] hover:bg-[var(--turquoise-hover)] text-white px-8 py-3 rounded-xl font-semibold text-sm transition whitespace-nowrap">
          Rechercher
        </button>
      </div>
    </div>
  </section>

  <!-- Events Grid -->
  <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <div class="flex items-center justify-between mb-8">
      <h2 class="text-2xl font-bold text-[var(--navy)]">Evenements recents</h2>
      <div class="text-sm text-[var(--slate)]">{{ filteredEvents.length }} evenement(s)</div>
    </div>

    <div v-if="loading" class="text-center py-20">
      <div class="inline-block w-8 h-8 border-4 border-[var(--turquoise)] border-t-transparent rounded-full animate-spin"></div>
    </div>

    <div v-else-if="!filteredEvents.length" class="text-center py-20 text-[var(--slate)]">
      Aucun evenement disponible pour le moment.
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <router-link
        v-for="event in filteredEvents"
        :key="event.id"
        :to="`/evenement/${event.slug}`"
        class="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
      >
        <div class="aspect-[16/10] bg-gradient-to-br from-[var(--turquoise)]/20 to-[var(--navy)]/10 relative overflow-hidden">
          <img v-if="event.cover_image" :src="event.cover_image" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
          <div v-else class="w-full h-full flex items-center justify-center">
            <svg class="w-16 h-16 text-[var(--turquoise)]/30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><circle cx="12" cy="13" r="3"/></svg>
          </div>
          <div class="absolute top-3 right-3 bg-green-500 text-white text-xs font-bold px-3 py-1 rounded-full">
            Photos en ligne
          </div>
        </div>
        <div class="p-5">
          <h3 class="font-bold text-[var(--navy)] text-lg mb-1 group-hover:text-[var(--turquoise)] transition-colors">{{ event.name }}</h3>
          <p class="text-sm text-[var(--slate)] mb-3">{{ formatDate(event.date) }}</p>
          <div class="flex items-center justify-between">
            <span class="text-xs text-[var(--slate)]">{{ event.photo_count }} photos</span>
            <span class="text-[var(--turquoise)] text-sm font-semibold group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
              Voir les photos
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </span>
          </div>
        </div>
      </router-link>
    </div>
  </section>

  <!-- Trust badges -->
  <section class="bg-white border-t border-[var(--beige)] py-12">
    <div class="max-w-5xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
      <div>
        <div class="w-12 h-12 bg-[var(--turquoise)]/10 rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6 text-[var(--turquoise)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
        </div>
        <p class="text-sm font-medium text-[var(--navy)]">Paiement securise</p>
        <p class="text-xs text-[var(--slate)] mt-1">SSL 256-bit</p>
      </div>
      <div>
        <div class="w-12 h-12 bg-[var(--turquoise)]/10 rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6 text-[var(--turquoise)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
        </div>
        <p class="text-sm font-medium text-[var(--navy)]">Telechargement HD</p>
        <p class="text-xs text-[var(--slate)] mt-1">Qualite originale</p>
      </div>
      <div>
        <div class="w-12 h-12 bg-[var(--turquoise)]/10 rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6 text-[var(--turquoise)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        </div>
        <p class="text-sm font-medium text-[var(--navy)]">Livraison instantanee</p>
        <p class="text-xs text-[var(--slate)] mt-1">Telechargement immediat</p>
      </div>
      <div>
        <div class="w-12 h-12 bg-[var(--turquoise)]/10 rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6 text-[var(--turquoise)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
        </div>
        <p class="text-sm font-medium text-[var(--navy)]">Support reactif</p>
        <p class="text-xs text-[var(--slate)] mt-1">Aide par email</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { webApi } from '../api/web.js'

const events = ref([])
const searchQuery = ref('')
const loading = ref(true)

const filteredEvents = computed(() => {
  if (!searchQuery.value) return events.value
  const q = searchQuery.value.toLowerCase()
  return events.value.filter(e => e.name.toLowerCase().includes(q))
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

onMounted(async () => {
  try {
    const res = await webApi.listEvents()
    events.value = res.data
  } catch (e) {
    console.error('Failed to load events:', e)
  } finally {
    loading.value = false
  }
})
</script>
