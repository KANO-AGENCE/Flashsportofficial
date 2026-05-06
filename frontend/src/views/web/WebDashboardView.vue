<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">E-commerce</h1>
        <p class="text-gray-500 text-sm">Gerez vos courses publiees sur le site web</p>
      </div>
      <span class="text-xs text-gray-400">Les courses web sont creees automatiquement depuis l'onglet Tri</span>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Courses publiees</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.published_events }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Photos indexees</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.total_photos }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Commandes</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.total_orders }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">CA Total</p>
        <p class="text-3xl font-bold text-green-600 mt-2">{{ stats.total_revenue }} EUR</p>
      </div>
    </div>

    <!-- Web Events List -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-100/60 flex items-center justify-between">
        <h2 class="font-semibold text-gray-900">Courses web</h2>
        <span class="text-xs text-gray-400">{{ webEvents.length }} course(s)</span>
      </div>

      <div v-if="!webEvents.length" class="p-8 text-center text-gray-400">
        Aucune course web. Cliquez sur "Ajouter une course" pour commencer.
      </div>

      <div v-else class="divide-y divide-gray-100/60">
        <div v-for="we in webEvents" :key="we.id" class="p-5 flex items-center gap-4 hover:bg-white/40 transition">
          <!-- Cover -->
          <div class="w-20 h-14 rounded-xl bg-gray-100/80 overflow-hidden shrink-0 relative group">
            <img v-if="we.cover_image" :src="we.cover_image" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-300">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/></svg>
            </div>
            <label class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center cursor-pointer">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/></svg>
              <input type="file" accept="image/*" class="hidden" @change="uploadCover(we.id, $event)" />
            </label>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="font-semibold text-gray-900 truncate">{{ we.event_name }}</h3>
              <span v-if="we.is_published" class="text-xs bg-green-100/80 text-green-700 px-2 py-0.5 rounded-full font-medium backdrop-blur-sm">En ligne</span>
              <span v-else class="text-xs bg-gray-100/80 text-gray-600 px-2 py-0.5 rounded-full font-medium backdrop-blur-sm">Brouillon</span>
            </div>
            <p class="text-sm text-gray-500">{{ we.event_date }} &middot; {{ we.photo_count || 0 }} photos &middot; {{ we.bib_count || 0 }} dossards &middot; /{{ we.slug }}</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 shrink-0">
            <button
              @click="togglePublish(we)"
              :class="we.is_published ? 'bg-gray-100/80 text-gray-700 hover:bg-gray-200/80' : 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40'"
              class="px-4 py-2 rounded-xl text-xs font-medium transition-all"
            >
              {{ we.is_published ? 'Depublier' : 'Mettre en ligne' }}
            </button>
            <button @click="deleteWebEvent(we.id)" class="text-red-400 hover:text-red-600 hover:bg-red-50/50 p-2 rounded-lg transition">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { webApi } from '../../api/events.js'
import api from '../../api/client.js'
import { useToast } from '../../composables/useToast'
const toast = useToast()

const stats = ref({ published_events: 0, total_photos: 0, total_orders: 0, total_revenue: 0 })
const webEvents = ref([])

async function loadData() {
  try {
    const [statsRes, eventsRes] = await Promise.all([
      webApi.stats(),
      webApi.listWebEvents(),
    ])
    stats.value = statsRes.data
    webEvents.value = eventsRes.data
  } catch (e) {
    console.error('Failed to load web data:', e)
  }
}

async function togglePublish(we) {
  await webApi.updateWebEvent(we.id, { is_published: !we.is_published })
  await loadData()
}

async function uploadCover(webEventId, event) {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    await webApi.uploadCover(webEventId, file)
    await loadData()
  } catch (e) {
    toast.error(e.response?.data?.detail || e.message)
  }
}

async function deleteWebEvent(id) {
  if (!confirm('Supprimer cette course web ?')) return
  try {
    await api.delete(`/web/admin/events/${id}`)
    await loadData()
  } catch (e) {
    toast.error(e.response?.data?.detail || e.message)
  }
}

onMounted(loadData)
</script>
