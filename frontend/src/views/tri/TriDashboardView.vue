<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Courses</h1>
        <p class="text-gray-500 mt-1">Module de tri photo</p>
      </div>
      <button
        @click="showCreateModal = true"
        class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Nouvelle course
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="text-center py-12 text-gray-400">Chargement...</div>

    <!-- Empty state -->
    <div v-else-if="!store.events.length" class="text-center py-16">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
      <h3 class="text-lg font-medium text-gray-600 mb-1">Aucune course</h3>
      <p class="text-gray-400">Cree ta premiere course pour commencer le tri</p>
    </div>

    <!-- Events grouped by month -->
    <div v-else>
      <div v-for="(group, monthLabel) in groupedEvents" :key="monthLabel" class="mb-8">
        <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">{{ monthLabel }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="ev in group"
            :key="ev.id"
            @click="router.push(`/tri/events/${ev.id}`)"
            class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5 cursor-pointer hover:shadow-xl hover:shadow-black/10 hover:border-blue-200/60 transition-all group"
          >
            <div class="flex items-start justify-between mb-3">
              <div>
                <h3 class="font-semibold text-gray-900 group-hover:text-blue-600 transition">{{ ev.name }}</h3>
                <p class="text-sm text-gray-400">{{ formatDate(ev.date) }}</p>
              </div>
              <span :class="statusClass(ev)" class="text-xs font-medium px-2.5 py-1 rounded-full backdrop-blur-sm">
                {{ statusText(ev) }}
              </span>
            </div>
            <div class="flex items-center gap-4 text-sm text-gray-500">
              <span>{{ ev.photo_count }} photos</span>
              <span v-if="ev.cards?.length">{{ ev.cards.length }} cartes</span>
              <span v-if="ev.stats">{{ ev.stats.unique_bibs }} dossards</span>
            </div>
            <div v-if="ev.photo_count > 0" class="mt-3">
              <div class="w-full bg-gray-200/50 rounded-full h-1.5">
                <div
                  class="bg-gradient-to-r from-blue-500 to-blue-400 h-1.5 rounded-full transition-all"
                  :style="{ width: (ev.processed_count / ev.photo_count * 100) + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showCreateModal = false">
      <div class="bg-white/90 backdrop-blur-2xl border border-white/60 shadow-2xl rounded-3xl w-full max-w-lg mx-4 p-6">
        <h2 class="text-lg font-semibold mb-4 text-gray-900">Nouvelle course</h2>
        <form @submit.prevent="createEvent" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
            <input v-model="newEvent.name" type="text" required class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="Triathlon de Nice 2025">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Date</label>
            <input v-model="newEvent.date" type="date" required class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button type="button" @click="showCreateModal = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl transition">Annuler</button>
            <button type="submit" :disabled="creating" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all disabled:opacity-50">
              {{ creating ? 'Creation...' : 'Creer' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '../../stores/events'
import { eventsApi } from '../../api/events'

const router = useRouter()
const store = useEventsStore()

const showCreateModal = ref(false)
const creating = ref(false)
const newEvent = ref({ name: '', date: '' })

onMounted(() => store.fetchEvents())

const groupedEvents = computed(() => {
  const groups = {}
  for (const ev of store.events) {
    const d = new Date(ev.date)
    const label = d.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
    if (!groups[label]) groups[label] = []
    groups[label].push(ev)
  }
  return groups
})

function formatDate(d) {
  return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

function statusText(ev) {
  if (!ev.photo_count) return 'Vide'
  if (ev.processed_count === 0) return 'Pret'
  if (ev.pending_count > 0) return 'En cours'
  return 'Termine'
}

function statusClass(ev) {
  const s = statusText(ev)
  const map = {
    'Vide': 'bg-gray-100/80 text-gray-600',
    'Pret': 'bg-blue-100/80 text-blue-700',
    'En cours': 'bg-blue-100/80 text-blue-700',
    'Termine': 'bg-green-100/80 text-green-700',
  }
  return map[s] || 'bg-gray-100/80 text-gray-600'
}

async function createEvent() {
  creating.value = true
  try {
    const res = await eventsApi.create(newEvent.value)
    showCreateModal.value = false
    newEvent.value = { name: '', date: '' }
    router.push(`/tri/events/${res.data.id}`)
  } finally {
    creating.value = false
  }
}
</script>
