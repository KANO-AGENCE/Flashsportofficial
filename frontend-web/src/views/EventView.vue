<template>
  <div v-if="loading" class="text-center py-20">
    <div class="inline-block w-8 h-8 border-4 border-[var(--turquoise)] border-t-transparent rounded-full animate-spin"></div>
  </div>

  <div v-else-if="!event" class="text-center py-20">
    <h2 class="text-xl font-bold text-[var(--navy)]">Evenement introuvable</h2>
    <router-link to="/" class="text-[var(--turquoise)] mt-4 inline-block">Retour a l'accueil</router-link>
  </div>

  <div v-else>
    <!-- Event Header -->
    <section class="bg-gradient-to-r from-[var(--navy)] to-[var(--slate)] text-white py-12">
      <div class="max-w-5xl mx-auto px-4">
        <router-link to="/" class="text-white/60 hover:text-white text-sm mb-4 inline-flex items-center gap-1 transition">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          Tous les evenements
        </router-link>
        <h1 class="font-display text-3xl sm:text-4xl font-bold mt-2">{{ event.name }}</h1>
        <p class="text-white/60 mt-2">{{ formatDate(event.date) }} &middot; {{ event.photo_count }} photos</p>
      </div>
    </section>

    <!-- Search by bib -->
    <section class="max-w-3xl mx-auto px-4 -mt-8">
      <div class="bg-white rounded-2xl shadow-xl p-6 sm:p-8">
        <h2 class="text-lg font-bold text-[var(--navy)] mb-1">Recherchez vos photos</h2>
        <p class="text-sm text-[var(--slate)] mb-5">Saisissez votre numero de dossard pour afficher vos photos.</p>

        <div class="flex gap-3">
          <div class="flex-1 relative">
            <input
              v-model="bibSearch"
              type="text"
              inputmode="numeric"
              pattern="[0-9]*"
              placeholder="Votre numero de dossard"
              class="w-full px-4 py-3 border-2 border-[var(--beige)] rounded-xl text-[var(--navy)] text-lg font-semibold focus:outline-none focus:border-[var(--turquoise)] transition placeholder:font-normal placeholder:text-base"
              @keydown.enter="searchBib"
            >
          </div>
          <button
            @click="searchBib"
            :disabled="!bibSearch.trim()"
            class="bg-[var(--turquoise)] hover:bg-[var(--turquoise-hover)] disabled:opacity-40 text-white px-8 py-3 rounded-xl font-semibold text-sm transition whitespace-nowrap"
          >
            Rechercher
          </button>
        </div>

        <!-- Autocomplete suggestions -->
        <div v-if="bibSearch && suggestions.length" class="mt-3 flex flex-wrap gap-2">
          <button
            v-for="bib in suggestions.slice(0, 10)"
            :key="bib"
            @click="bibSearch = bib; searchBib()"
            class="px-3 py-1.5 bg-[var(--beige-light)] hover:bg-[var(--turquoise)] hover:text-white text-sm text-[var(--navy)] rounded-lg transition font-medium"
          >
            #{{ bib }}
          </button>
          <span v-if="suggestions.length > 10" class="text-xs text-[var(--slate)] self-center">+{{ suggestions.length - 10 }} autres</span>
        </div>

        <p class="text-xs text-[var(--slate)] mt-4 flex items-center gap-1">
          <svg class="w-3.5 h-3.5 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/></svg>
          Votre recherche est securisee et confidentielle.
        </p>
      </div>
    </section>

    <!-- Event description -->
    <section v-if="event.description" class="max-w-3xl mx-auto px-4 mt-8">
      <p class="text-[var(--slate)] text-sm">{{ event.description }}</p>
    </section>

    <!-- CTA -->
    <section class="max-w-3xl mx-auto px-4 mt-12 text-center">
      <p class="text-[var(--slate)]">Recherchez votre dossard pour decouvrir vos photos et les offres disponibles.</p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { webApi } from '../api/web.js'

const route = useRoute()
const router = useRouter()

const event = ref(null)
const loading = ref(true)
const bibSearch = ref('')

const suggestions = computed(() => {
  if (!event.value?.bib_numbers || !bibSearch.value) return []
  const q = bibSearch.value
  return event.value.bib_numbers.filter(b => b.startsWith(q))
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

function searchBib() {
  const bib = bibSearch.value.trim()
  if (!bib) return
  router.push(`/evenement/${route.params.slug}/dossard/${bib}`)
}

onMounted(async () => {
  try {
    const res = await webApi.getEvent(route.params.slug)
    event.value = res.data
  } catch (e) {
    console.error('Failed to load event:', e)
  } finally {
    loading.value = false
  }
})
</script>
