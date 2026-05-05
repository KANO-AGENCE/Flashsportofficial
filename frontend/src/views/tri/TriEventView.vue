<template>
  <div class="p-6" v-if="event">
    <!-- Header -->
    <div class="flex items-center gap-4 mb-6">
      <button @click="router.push('/tri')" class="text-gray-400 hover:text-gray-600 hover:bg-white/50 p-1.5 rounded-xl transition">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <div class="flex-1">
        <h1 class="text-2xl font-bold text-gray-900">{{ event.name }}</h1>
        <p class="text-gray-500">{{ formatDate(event.date) }}</p>
      </div>
      <button @click="showSettings = !showSettings" class="text-gray-400 hover:text-gray-600 hover:bg-white/50 p-2 rounded-xl transition">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
      </button>
      <button @click="confirmDelete" class="text-red-400 hover:text-red-600 hover:bg-red-50/50 p-2 rounded-xl transition" title="Supprimer">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
      </button>
    </div>

    <!-- Global Stats -->
    <div v-if="event.stats" class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4 text-center">
        <p class="text-2xl font-bold text-gray-900">{{ event.photo_count }}</p>
        <p class="text-xs text-gray-400 uppercase tracking-wider mt-1">Photos</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4 text-center">
        <p class="text-2xl font-bold text-blue-600">{{ event.stats.bon }}</p>
        <p class="text-xs text-gray-400 uppercase tracking-wider mt-1">Bons</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4 text-center">
        <p class="text-2xl font-bold text-gray-500">{{ event.stats.incertain }}</p>
        <p class="text-xs text-gray-400 uppercase tracking-wider mt-1">Incertains</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4 text-center">
        <p class="text-2xl font-bold text-blue-600">{{ event.stats.unique_bibs }}</p>
        <p class="text-xs text-gray-400 uppercase tracking-wider mt-1">Dossards</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4 text-center">
        <p class="text-2xl font-bold text-gray-600">{{ event.stats.validated }}</p>
        <p class="text-xs text-gray-400 uppercase tracking-wider mt-1">Valides</p>
      </div>
    </div>

    <!-- Settings panel -->
    <div v-if="showSettings" class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-6 mb-6">
      <h3 class="font-semibold mb-4 text-gray-900">Parametres IA</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm text-gray-600 mb-1">Seuil de flou</label>
          <input type="range" v-model.number="config.blur_threshold" min="20" max="200" class="w-full">
          <span class="text-sm text-gray-500">{{ config.blur_threshold }}</span>
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">Confiance YOLO (%)</label>
          <input type="range" v-model.number="config.yolo_confidence" min="10" max="80" class="w-full">
          <span class="text-sm text-gray-500">{{ config.yolo_confidence }}%</span>
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">Chiffres dossard</label>
          <div class="flex items-center gap-2">
            <input type="number" v-model.number="config.bib_min_digits" min="1" max="6" class="w-16 px-2 py-1 bg-white/50 border border-gray-200/60 rounded-xl backdrop-blur-sm outline-none">
            <span>a</span>
            <input type="number" v-model.number="config.bib_max_digits" min="1" max="6" class="w-16 px-2 py-1 bg-white/50 border border-gray-200/60 rounded-xl backdrop-blur-sm outline-none">
          </div>
        </div>
      </div>
      <button @click="saveConfig" class="mt-4 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">Sauvegarder</button>
    </div>

    <!-- Cards -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl mb-6">
      <div class="flex items-center justify-between p-4 border-b border-gray-100/60">
        <h3 class="font-semibold text-gray-900">Cartes</h3>
        <button @click="showImport = true" class="text-blue-600 hover:text-blue-500 text-sm font-medium transition">+ Importer</button>
      </div>
      <div v-if="!event.cards?.length" class="p-8 text-center text-gray-400">Aucune carte importee</div>
      <div v-else class="divide-y divide-gray-100/60">
        <div v-for="card in event.cards" :key="card.id" class="p-4">
          <!-- Card header -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 backdrop-blur-sm"
                :class="cardIconBg(card)">
                <svg v-if="card.status === 'importing'" class="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                <svg v-else-if="isCardProcessing(card.id)" class="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                <svg v-else-if="card.processed_count === card.photo_count && card.photo_count > 0" class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                <svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
              </div>
              <div>
                <p class="font-medium text-gray-800">{{ card.name }}</p>
                <p class="text-sm text-gray-500">{{ card.photo_count }} photos <span v-if="card.total_expected">/ {{ card.total_expected }}</span></p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span :class="cardStatusClass(card)" class="text-xs font-medium px-2.5 py-1 rounded-full backdrop-blur-sm">{{ cardStatusText(card) }}</span>
              <button @click="deleteCard(card.id)" class="text-red-400 hover:text-red-600 p-1 hover:bg-red-50/50 rounded-lg transition">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
          </div>

          <!-- Card stats -->
          <div v-if="card.photo_count > 0" class="mb-3">
            <div class="flex items-center gap-4 text-xs text-gray-500 mb-2">
              <span class="text-blue-600 font-medium">{{ card.processed_count }} traitees</span>
              <span v-if="card.pending_count > 0" class="text-gray-500 font-medium">{{ card.pending_count }} en attente</span>
              <span class="text-blue-600 font-medium">{{ card.validated_count }} validees</span>
              <span class="text-gray-600 font-medium">{{ card.unique_bibs }} dossards</span>
            </div>
            <div class="w-full bg-gray-200/50 rounded-full h-1.5">
              <div class="h-1.5 rounded-full transition-all bg-gradient-to-r"
                :class="card.pending_count === 0 ? 'from-green-500 to-green-400' : 'from-blue-500 to-blue-400'"
                :style="{ width: (card.processed_count / card.photo_count * 100) + '%' }"></div>
            </div>
          </div>

          <!-- Card actions -->
          <div class="flex items-center gap-2 flex-wrap">
            <button
              v-if="card.pending_count > 0 && !isCardProcessing(card.id)"
              @click="processCard(card)"
              class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-xs font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
            >
              Traiter ({{ card.pending_count }})
            </button>
            <span v-if="isCardProcessing(card.id)" class="text-xs text-blue-600 font-medium flex items-center gap-1">
              <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              Traitement...
            </span>
            <button
              v-if="card.processed_count > 0"
              @click="router.push(`/tri/events/${event.id}/photos?card_id=${card.id}`)"
              class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-xs font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
            >
              Resultats ({{ card.processed_count }})
            </button>
            <button
              v-if="card.processed_count > 0"
              @click="router.push(`/tri/events/${event.id}/photos?card_id=${card.id}&verif=1`)"
              class="bg-blue-500 hover:bg-blue-400 text-white px-4 py-2 rounded-xl text-xs font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
            >
              Mode Verif
            </button>
          </div>

          <!-- Processing progress for this card -->
          <div v-if="isCardProcessing(card.id) && cardStatuses[card.id]" class="mt-3 bg-gray-50/80 backdrop-blur-sm rounded-xl p-3 border border-gray-100/60">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-gray-600">Traitement en cours...</span>
              <span class="text-xs text-gray-500">{{ cardStatuses[card.id].processed }} / {{ cardStatuses[card.id].total }}</span>
            </div>
            <div class="w-full bg-gray-200/50 rounded-full h-1.5">
              <div class="bg-gradient-to-r from-blue-500 to-blue-400 h-1.5 rounded-full transition-all"
                :style="{ width: cardProgressPct(card.id) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Global actions -->
    <div class="flex items-center gap-3 mb-6 flex-wrap">
      <button
        v-if="event.pending_count > 0"
        @click="launchProcess"
        class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
      >
        Traiter TOUT ({{ event.pending_count }} photos)
      </button>
      <button
        v-if="processing"
        @click="stopProcess"
        class="bg-red-500 hover:bg-red-400 text-white px-6 py-3 rounded-xl font-medium shadow-lg shadow-red-500/25 hover:shadow-red-500/40 transition-all"
      >
        STOP
      </button>
      <button
        v-if="event.processed_count > 0"
        @click="router.push(`/tri/events/${event.id}/photos`)"
        class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
      >
        Voir tous les resultats
      </button>
      <button
        v-if="event.processed_count > 0"
        @click="router.push(`/tri/events/${event.id}/photos?verif=1`)"
        class="bg-blue-500 hover:bg-blue-400 text-white px-6 py-3 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
      >
        Verif globale
      </button>
      <button
        v-if="event.processed_count > 0"
        @click="publishToWeb"
        :disabled="publishing"
        class="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
      >
        {{ publishing ? 'Publication...' : 'Publier sur le web' }}
      </button>
      <button
        v-if="event.processed_count > 0"
        @click="resetProcess"
        class="text-red-500 hover:text-red-700 hover:bg-white/50 px-4 py-3 rounded-xl font-medium text-sm transition"
      >
        Reset
      </button>
    </div>

    <!-- Processing progress (global) -->
    <div v-if="processing && !processingCardId" class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4 mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Traitement en cours...</span>
        <span class="text-sm text-gray-500">{{ processStatus.processed }} / {{ processStatus.total }}</span>
      </div>
      <div class="w-full bg-gray-200/50 rounded-full h-2">
        <div class="bg-gradient-to-r from-blue-500 to-blue-400 h-2 rounded-full transition-all" :style="{ width: progressPct + '%' }"></div>
      </div>
    </div>

    <!-- Import modal -->
    <div v-if="showImport" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showImport = false">
      <div class="bg-white/90 backdrop-blur-2xl border border-white/60 shadow-2xl rounded-3xl w-full max-w-lg mx-4 p-6">
        <h2 class="text-lg font-semibold mb-4 text-gray-900">Importer une carte</h2>

        <!-- Tab selector -->
        <div class="flex border-b border-gray-200/60 mb-4">
          <button
            @click="importMode = 'folder'"
            :class="importMode === 'folder' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            class="flex-1 pb-2 text-sm font-medium border-b-2 transition"
          >
            Chemin dossier
          </button>
          <button
            @click="importMode = 'files'"
            :class="importMode === 'files' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            class="flex-1 pb-2 text-sm font-medium border-b-2 transition"
          >
            Parcourir fichiers
          </button>
        </div>

        <!-- Mode: folder path -->
        <form v-if="importMode === 'folder'" @submit.prevent="importFolder" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Chemin du dossier</label>
            <input v-model="importPath" type="text" required class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="/Volumes/CARTE_SD/DCIM">
          </div>
          <div class="flex justify-end gap-3">
            <button type="button" @click="showImport = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl transition">Annuler</button>
            <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">Importer</button>
          </div>
        </form>

        <!-- Mode: file picker -->
        <div v-else class="space-y-4">
          <div
            @dragover.prevent="dragOver = true"
            @dragleave="dragOver = false"
            @drop.prevent="handleDrop"
            :class="dragOver ? 'border-blue-500 bg-blue-50/50' : 'border-gray-300/60'"
            class="border-2 border-dashed rounded-2xl p-8 text-center transition cursor-pointer bg-white/30 backdrop-blur-sm"
            @click="$refs.fileInput.click()"
          >
            <svg class="w-10 h-10 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
            <p class="text-sm text-gray-600 font-medium">Glisse tes photos ici ou clique pour parcourir</p>
            <p class="text-xs text-gray-400 mt-1">JPG, PNG, TIFF, RAW...</p>
            <input
              ref="fileInput"
              type="file"
              multiple
              accept="image/*,.cr2,.nef,.arw,.tiff,.tif"
              class="hidden"
              @change="handleFileSelect"
            >
          </div>

          <div v-if="selectedFiles.length" class="bg-gray-50/80 backdrop-blur-sm rounded-xl p-3 border border-gray-100/60">
            <p class="text-sm font-medium text-gray-700 mb-1">{{ selectedFiles.length }} fichier(s) selectionne(s)</p>
            <p class="text-xs text-gray-500">{{ formatFileSize(totalFileSize) }}</p>
          </div>

          <div v-if="uploading" class="w-full bg-gray-200/50 rounded-full h-2">
            <div class="bg-gradient-to-r from-blue-500 to-blue-400 h-2 rounded-full transition-all" :style="{ width: uploadProgress + '%' }"></div>
          </div>

          <div class="flex justify-end gap-3">
            <button type="button" @click="showImport = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl transition">Annuler</button>
            <button
              @click="uploadFiles"
              :disabled="!selectedFiles.length || uploading"
              class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all disabled:opacity-50"
            >
              {{ uploading ? 'Upload en cours...' : 'Uploader' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="p-6 text-center text-gray-400">Chargement...</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { eventsApi } from '../../api/events'
import { photosApi } from '../../api/photos'
import { useToast } from '../../composables/useToast'
const toast = useToast()

const route = useRoute()
const router = useRouter()

const event = ref(null)
const showSettings = ref(false)
const showImport = ref(false)
const importMode = ref('folder')
const importPath = ref('')
const selectedFiles = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const dragOver = ref(false)
const processing = ref(false)
const publishing = ref(false)
const processStatus = ref({ total: 0, processed: 0 })
// Multi-card processing: track which cards are being processed + their status
const processingCards = ref(new Set())
const cardStatuses = ref({}) // { cardId: { total, processed, pending } }
const config = ref({ blur_threshold: 40, yolo_confidence: 35, bib_min_digits: 1, bib_max_digits: 5 })

let pollTimer = null

const progressPct = computed(() => {
  if (!processStatus.value.total) return 0
  return Math.round(processStatus.value.processed / processStatus.value.total * 100)
})

function isCardProcessing(cardId) {
  return processingCards.value.has(cardId)
}

function cardProgressPct(cardId) {
  const s = cardStatuses.value[cardId]
  if (!s || !s.total) return 0
  return Math.round(s.processed / s.total * 100)
}

// Derive card display status from actual state
function getCardState(card) {
  if (card.status === 'importing') return 'importing'
  if (isCardProcessing(card.id)) return 'processing'
  if (card.processed_count === card.photo_count && card.photo_count > 0) return 'done'
  return 'pending'
}

function cardIconBg(card) {
  const state = getCardState(card)
  if (state === 'done') return 'bg-green-100/80'
  if (state === 'importing' || state === 'processing') return 'bg-blue-100/80'
  return 'bg-gray-100/80'
}

function cardStatusClass(card) {
  const state = getCardState(card)
  const map = {
    pending: 'bg-gray-100/80 text-gray-600',
    importing: 'bg-blue-100/80 text-blue-700',
    processing: 'bg-blue-100/80 text-blue-700',
    done: 'bg-green-100/80 text-green-700',
    error: 'bg-red-100/80 text-red-700',
  }
  return map[state] || 'bg-gray-100/80 text-gray-600'
}

function cardStatusText(card) {
  const state = getCardState(card)
  const map = {
    pending: 'En attente',
    importing: 'Import...',
    processing: 'Traitement...',
    done: 'Termine',
    error: 'Erreur',
  }
  // Also handle raw DB statuses that don't map to computed states
  if (card.status === 'error') return 'Erreur'
  if (card.status === 'stopped') return 'Stoppe'
  if (card.status === 'locked') return 'Gele'
  return map[state] || 'En attente'
}

async function loadEvent() {
  const res = await eventsApi.get(route.params.id)
  event.value = res.data
  config.value = {
    blur_threshold: res.data.blur_threshold,
    yolo_confidence: Math.round(res.data.yolo_confidence * 100),
    bib_min_digits: res.data.bib_min_digits,
    bib_max_digits: res.data.bib_max_digits,
  }
  // Detect if any processing is active (reload scenario)
  if (res.data.pending_count > 0 && res.data.processed_count > 0 && !pollTimer) {
    // Check if there are cards with pending photos that might be processing
    processing.value = true
    startMultiCardPolling()
  }
}

async function saveConfig() {
  await eventsApi.updateConfig(event.value.id, {
    blur_threshold: config.value.blur_threshold,
    yolo_confidence: config.value.yolo_confidence / 100,
    bib_min_digits: config.value.bib_min_digits,
    bib_max_digits: config.value.bib_max_digits,
  })
  showSettings.value = false
  await loadEvent()
}

async function importFolder() {
  await photosApi.importFolder(event.value.id, importPath.value)
  showImport.value = false
  importPath.value = ''
  const cardPoll = setInterval(async () => {
    await loadEvent()
    const importing = event.value.cards?.some(c => c.status === 'importing' || c.status === 'pending')
    if (!importing) clearInterval(cardPoll)
  }, 2000)
}

function handleFileSelect(e) {
  selectedFiles.value = Array.from(e.target.files)
}

function handleDrop(e) {
  dragOver.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/') || /\.(cr2|nef|arw|tiff|tif)$/i.test(f.name))
  selectedFiles.value = files
}

const totalFileSize = computed(() => selectedFiles.value.reduce((sum, f) => sum + f.size, 0))

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' o'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' Mo'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' Go'
}

async function uploadFiles() {
  if (!selectedFiles.value.length) return
  uploading.value = true
  uploadProgress.value = 0

  const cardName = `Upload ${new Date().toLocaleString('fr-FR')}`
  const cardRes = await photosApi.createCard(event.value.id, cardName)
  const cardId = cardRes.data.id

  const batchSize = 10
  const total = selectedFiles.value.length
  let uploaded = 0

  for (let i = 0; i < total; i += batchSize) {
    const batch = selectedFiles.value.slice(i, i + batchSize)
    await photosApi.upload(event.value.id, batch, cardId)
    uploaded += batch.length
    uploadProgress.value = Math.round(uploaded / total * 100)
  }

  uploading.value = false
  selectedFiles.value = []
  showImport.value = false
  await loadEvent()
}

// --- Processing per card ---
async function processCard(card) {
  const res = await photosApi.processCard(event.value.id, card.id)
  if (res.data.message.includes('already')) {
    toast.warn(res.data.message)
    return
  }
  processingCards.value = new Set([...processingCards.value, card.id])
  startMultiCardPolling()
}

function startMultiCardPolling() {
  if (pollTimer) return // already polling
  pollTimer = setInterval(async () => {
    if (!processingCards.value.size && !processing.value) {
      stopPolling()
      return
    }

    // Poll each card
    const cardIds = [...processingCards.value]
    const finished = []
    for (const cid of cardIds) {
      try {
        const res = await photosApi.processStatus(event.value.id, cid)
        cardStatuses.value = { ...cardStatuses.value, [cid]: res.data }
        if (res.data.pending === 0) finished.push(cid)
      } catch { finished.push(cid) }
    }

    // Poll global if full-event processing
    if (processing.value) {
      const res = await photosApi.processStatus(event.value.id)
      processStatus.value = res.data
      if (res.data.pending === 0) processing.value = false
    }

    // Clean up finished cards
    if (finished.length) {
      const next = new Set(processingCards.value)
      finished.forEach(cid => {
        next.delete(cid)
        delete cardStatuses.value[cid]
      })
      processingCards.value = next
      await loadEvent()
    }

    // Stop polling if nothing left
    if (!processingCards.value.size && !processing.value) {
      stopPolling()
    }
  }, 2000)
}

// --- Processing global ---
async function launchProcess() {
  await photosApi.process(event.value.id)
  processing.value = true
  startMultiCardPolling()
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function stopProcess() {
  await photosApi.stop(event.value.id)
  processing.value = false
  processingCards.value = new Set()
  cardStatuses.value = {}
  stopPolling()
  await loadEvent()
}

async function resetProcess() {
  if (!confirm('Reset le traitement ? Les detections seront supprimees.')) return
  await photosApi.reset(event.value.id)
  await loadEvent()
}

async function publishToWeb() {
  publishing.value = true
  try {
    const res = await photosApi.publishToWeb(event.value.id)
    toast.success(`Publication reussie : ${res.data.published} photos, ${res.data.unique_bibs} dossards indexes.`)
  } catch (e) {
    toast.error('Publication: ' + (e.response?.data?.detail || e.message))
  } finally {
    publishing.value = false
  }
}

async function deleteCard(cardId) {
  if (!confirm('Supprimer cette carte et ses photos ?')) return
  await photosApi.deleteCard(cardId)
  await loadEvent()
}

async function confirmDelete() {
  if (!confirm(`Supprimer la course "${event.value.name}" et toutes ses photos ?`)) return
  await eventsApi.delete(event.value.id)
  router.push('/tri')
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

onMounted(loadEvent)
onUnmounted(stopPolling)
</script>
