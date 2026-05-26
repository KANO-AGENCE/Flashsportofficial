<template>
  <div class="h-full flex flex-col">
    <!-- Header (list view) -->
    <div v-if="!viewerOpen" class="px-6 py-4 bg-white/70 backdrop-blur-xl border-b border-white/60 flex items-center gap-4 shrink-0">
      <button @click="router.push(`/tri/events/${route.params.id}`)" class="text-gray-400 hover:text-gray-600 transition">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <h1 class="text-lg font-bold text-gray-900 flex-1">
        Resultats
        <span v-if="cardName" class="text-sm font-normal text-gray-500 ml-2">— {{ cardName }}</span>
      </h1>
      <div class="flex items-center gap-2">
        <select v-model="filter" class="px-3 py-1.5 bg-white/50 border border-gray-200/60 rounded-xl text-sm backdrop-blur-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 outline-none">
          <option value="">Toutes</option>
          <option value="bon">Bons</option>
          <option value="mauvais">Mauvais</option>
          <option value="flou">Flous</option>
          <option value="coupe">Coupes</option>
          <option value="incertain">Incertains</option>
        </select>
        <input v-model="bibSearch" type="text" placeholder="Dossard..." class="px-3 py-1.5 bg-white/50 border border-gray-200/60 rounded-xl text-sm w-28 backdrop-blur-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 outline-none">
      </div>
      <button @click="startVerifMode" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg shadow-blue-500/25 transition-all hover:shadow-blue-500/40">
        Mode Verification
      </button>
    </div>

    <!-- Photo list (non-verif) -->
    <div v-if="!viewerOpen" class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-center py-12 text-gray-400">Chargement...</div>
      <div v-else-if="!filteredPhotos.length" class="text-center py-12 text-gray-400">Aucune photo</div>
      <div v-else class="space-y-3">
        <div
          v-for="(photo, idx) in filteredPhotos" :key="photo.id"
          @click="openViewer(idx)"
          class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-lg shadow-black/5 hover:border-blue-300/60 hover:shadow-blue-500/10 transition-all cursor-pointer flex items-center gap-4 p-3"
        >
          <div class="w-20 h-20 rounded-xl overflow-hidden bg-gray-100/80 shrink-0">
            <img :src="photoUrl(photo)" class="w-full h-full object-cover" loading="lazy">
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <template v-for="det in visibleDets(photo)" :key="det.id">
                <span v-if="effectiveBib(det)" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-green-100/80 text-green-700">#{{ effectiveBib(det) }}</span>
                <span v-else class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-gray-100/80 text-gray-500">?</span>
              </template>
              <span v-if="!photo.detections.length" class="text-xs text-red-400">Aucune detection</span>
            </div>
            <p class="text-sm text-gray-500 truncate">{{ photo.filename }}</p>
          </div>
          <span :class="classificationBadge(photo)" class="text-xs font-medium px-2.5 py-1 rounded-full">{{ classificationLabel(photo) }}</span>
        </div>
      </div>
    </div>

    <!-- ========== VERIF / VIEWER — LAYOUT PRO ========== -->
    <div v-if="viewerOpen" class="fixed inset-0 bg-gray-950 z-50 flex flex-col">

      <!-- Top bar -->
      <div class="flex items-center gap-3 px-3 py-2 bg-gray-900 border-b border-gray-800 shrink-0">
        <button @click="closeViewer" class="text-gray-400 hover:text-white transition p-1">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
        <span class="text-sm font-bold text-white">Photo {{ viewerIdx + 1 }} / {{ sessionPhotos.length }}</span>
        <div class="flex items-center gap-1 ml-2">
          <span :class="statusDot(currentVerifStatus)" class="w-2.5 h-2.5 rounded-full inline-block"></span>
          <span class="text-xs text-gray-400">{{ statusLabel(currentVerifStatus) }}</span>
        </div>

        <!-- Session filters -->
        <div class="flex items-center gap-1 ml-4">
          <button v-for="f in sessionFilters" :key="f.key"
            @click="setSessionFilter(f.key)"
            :class="sessionFilter === f.key ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'"
            class="text-[11px] px-2 py-1 rounded-md transition font-medium">
            {{ f.label }} {{ f.count }}
          </button>
        </div>

        <div class="flex-1"></div>
        <button v-if="lastValidatedIdx >= 0 && verifDoneCount < sessionPhotos.length"
          @click="goToNextPending"
          class="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded-lg font-medium transition shadow-lg shadow-blue-600/20 flex items-center gap-1.5"
          title="Revenir a la prochaine photo a verifier">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"/></svg>
          A traiter
        </button>
        <span class="text-xs text-gray-500">{{ verifDoneCount }}/{{ sessionPhotos.length }} verifiees</span>
        <!-- Secondary toggle -->
        <button v-if="hiddenDetsCount > 0"
          @click="showSecondary = !showSecondary"
          :class="showSecondary ? 'text-blue-400' : 'text-gray-600'"
          class="text-[11px] hover:text-gray-300 transition ml-2">
          +{{ hiddenDetsCount }} det.
        </button>
      </div>

      <!-- Main area: sidebar + photo -->
      <div class="flex-1 flex overflow-hidden">

        <!-- ===== LEFT — NEXT PHOTO PREVIEW ===== -->
        <div class="w-[380px] bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
          <!-- Next photo preview -->
          <div v-if="nextPendingPhoto" class="flex-1 flex flex-col p-3">
            <div class="text-xs text-gray-500 mb-1.5 flex items-center gap-2">
              <span>Suivante</span>
              <span class="font-mono">{{ photoIndex(nextPendingPhoto) }}</span>
              <span v-if="nextPendingBibs" class="text-green-400 font-bold font-mono text-sm">{{ nextPendingBibs }}</span>
              <span v-else class="text-red-400 font-bold text-sm">?</span>
            </div>
            <div @click="goToPhoto(nextPendingPhoto)" class="flex-1 rounded-xl overflow-hidden cursor-pointer border-2 transition relative"
              :class="nextPhotoPreviewBorder">
              <img :src="photoUrl(nextPendingPhoto)" class="w-full h-full object-contain bg-gray-950">
            </div>
          </div>
          <div v-else class="flex-1 flex items-center justify-center">
            <span class="text-sm text-gray-600">Toutes traitees</span>
          </div>
          <!-- Progress summary -->
          <div class="p-2 border-t border-gray-800">
            <div class="flex items-center gap-1.5 mb-1.5">
              <span :class="statusDot('validated')" class="w-2 h-2 rounded-full"></span>
              <span class="text-[10px] text-gray-400">{{ sessionFilters.find(f => f.key === 'validated')?.count || 0 }}</span>
              <span :class="statusDot('rejected')" class="w-2 h-2 rounded-full ml-1"></span>
              <span class="text-[10px] text-gray-400">{{ sessionFilters.find(f => f.key === 'rejected')?.count || 0 }}</span>
              <span :class="statusDot('pending')" class="w-2 h-2 rounded-full ml-1"></span>
              <span class="text-[10px] text-gray-400">{{ sessionFilters.find(f => f.key === 'pending')?.count || 0 }}</span>
            </div>
            <div class="w-full bg-gray-800 rounded-full h-1.5">
              <div class="bg-green-500 h-1.5 rounded-full transition-all" :style="{ width: progressPct + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- ===== MAIN PHOTO ===== -->
        <div class="flex-1 flex flex-col bg-black">
          <!-- Photo area -->
          <div class="flex-1 flex items-center justify-center relative overflow-hidden transition-all duration-200" ref="imgWrap"
            :class="{
              'ring-4 ring-inset ring-green-500/30': currentPhotoSignal === 'good',
              'ring-4 ring-inset ring-red-500/30': currentPhotoSignal === 'bad',
              'ring-4 ring-inset ring-amber-500/30': currentPhotoSignal === 'noBib',
            }">
            <!-- Preload next image -->
            <link v-if="nextPhoto" rel="prefetch" :href="photoUrl(nextPhoto)">

            <img
              v-if="currentPhoto"
              ref="viewerImg"
              :src="photoUrl(currentPhoto) + cacheBust(currentPhoto)"
              :class="['max-w-full max-h-full object-contain transition-opacity duration-100', flashClass]"
              @load="onImgLoad"
              @mouseenter="zoomActive = true"
              @mouseleave="zoomActive = false"
              @mousemove="onZoomMove"
            >
            <canvas ref="bboxCanvas" class="absolute pointer-events-none"></canvas>

            <!-- Zoom lens -->
            <div v-show="zoomActive" ref="zoomLens"
              class="absolute pointer-events-none border-2 border-white/40 rounded-lg shadow-xl"
              :style="{ width: '300px', height: '200px', ...zoomStyle }"></div>

            <!-- Nav arrows -->
            <button @click="viewerNav(-1)" class="absolute left-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/70 text-white/80 hover:text-white rounded-full p-2.5 transition">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
            </button>
            <button @click="viewerNav(1)" class="absolute right-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/70 text-white/80 hover:text-white rounded-full p-2.5 transition">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </button>

            <!-- Validated overlay badge -->
            <div v-if="currentVerifStatus === 'validated'" class="absolute top-3 right-3 bg-green-600/90 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-lg">Valide</div>
            <div v-else-if="currentVerifStatus === 'rejected'" class="absolute top-3 right-3 bg-red-600/90 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-lg">Rejete</div>

            <!-- Detection status indicator (top-left) -->
            <div v-if="currentVerifStatus === 'pending'" class="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-bold shadow-lg"
              :class="{
                'bg-green-600/90 text-white': currentPhotoSignal === 'good',
                'bg-red-600/90 text-white': currentPhotoSignal === 'bad',
                'bg-amber-500/90 text-white': currentPhotoSignal === 'noBib',
              }">
              <span v-if="currentPhotoSignal === 'good'">DOSSARD</span>
              <span v-else-if="currentPhotoSignal === 'bad'">MAUVAISE</span>
              <span v-else-if="currentPhotoSignal === 'noBib'">PAS DE DOSSARD</span>
            </div>
          </div>

          <!-- ===== BOTTOM BAR ===== -->
          <div class="px-4 py-2.5 bg-gray-900 border-t border-gray-800 shrink-0">
            <div class="flex items-center gap-3">
              <input
                ref="bibInput"
                v-model="bibFieldValue"
                type="text"
                :placeholder="bibPlaceholder"
                class="flex-1 bg-gray-800 border-2 text-white px-4 py-2 rounded-xl text-lg font-mono tracking-wider focus:outline-none transition"
                :class="bibInputBorder"
                @keydown.enter.prevent="validateAndNext"
              >
              <button @click="validateAndNext" class="bg-green-600 hover:bg-green-500 text-white px-5 py-2 rounded-xl text-sm font-bold transition shadow-lg shadow-green-600/20">Entree</button>
              <button @click="rejectAndNext" class="bg-red-600 hover:bg-red-500 text-white px-3 py-2 rounded-xl text-sm font-bold transition" title="Rejeter (raccourci: A)">Rejeter</button>
              <button @click="vUndo" :disabled="!history.length" class="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-xl text-sm font-medium transition disabled:opacity-30">Z</button>
              <button @click="vRotate" class="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-xl text-sm font-medium transition">R</button>
            </div>
            <div class="flex items-center justify-between mt-1">
              <span class="text-[10px] text-gray-600">Entree=Valider | A/x=Rejeter | Z=Annuler | R=Rotation | &amp;=A traiter</span>
              <span v-if="currentVisibleDets.length > 1" class="text-[10px] text-blue-400">{{ currentVisibleDets.length }} personnes — espaces entre les dossards</span>
              <span v-else-if="bibFieldValue === '90000'" class="text-[10px] text-amber-400">Pas de dossard lu — 90000 par defaut</span>
              <span class="text-[10px] text-gray-600 font-mono">{{ currentPhoto?.filename }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { photosApi } from '../../api/photos'
import { useToast } from '../../composables/useToast'
const toast = useToast()

const route = useRoute()
const router = useRouter()

// --- DOM refs ---
const viewerEl = ref(null)
const viewerImg = ref(null)
const bboxCanvas = ref(null)
const imgWrap = ref(null)
const zoomLens = ref(null)
const bibInput = ref(null)

// --- Data ---
const allPhotos = ref([])
const loading = ref(false)
const filter = ref('')
const bibSearch = ref('')

// --- Viewer state ---
const viewerOpen = ref(false)
const sessionPhotos = ref([])  // FULL session — never modified
const viewerIdx = ref(0)
const bibFieldValue = ref('')
const history = ref([])
const flashClass = ref('')
const showSecondary = ref(false)

// --- Zoom ---
const zoomActive = ref(false)
const zoomStyle = ref({})
const ZOOM_FACTOR = 3

// --- Session ---
const verifMode = ref(false)
const sessionFilter = ref('all')

const SECONDARY_THRESHOLD = 0.15
const lastValidatedIdx = ref(-1)

const eventId = computed(() => route.params.id)
const cardId = computed(() => route.query.card_id || null)
const autoVerif = computed(() => route.query.verif === '1')
const cardName = ref('')

// ============================================================
// COMPUTED
// ============================================================

const filteredPhotos = computed(() => {
  let list = allPhotos.value
  if (bibSearch.value) {
    list = list.filter(p => p.detections.some(d => effectiveBib(d)?.includes(bibSearch.value)))
  }
  if (filter.value) {
    list = list.filter(p => {
      if (!p.detections.length) return filter.value === 'mauvais'
      return p.detections.some(d => effectiveClass(d) === filter.value)
    })
  }
  return list
})

const currentPhoto = computed(() => sessionPhotos.value[viewerIdx.value] || null)
const nextPhoto = computed(() => sessionPhotos.value[viewerIdx.value + 1] || null)

// Next pending photo (for left sidebar preview)
const nextPendingPhoto = computed(() => {
  for (let offset = 1; offset < sessionPhotos.value.length; offset++) {
    const idx = (viewerIdx.value + offset) % sessionPhotos.value.length
    if (photoVerifStatus(sessionPhotos.value[idx]) === 'pending') {
      return sessionPhotos.value[idx]
    }
  }
  return null
})

const nextPendingBibs = computed(() => {
  if (!nextPendingPhoto.value) return ''
  return photoBibSummary(nextPendingPhoto.value)
})

const nextPhotoPreviewBorder = computed(() => {
  const p = nextPendingPhoto.value
  if (!p) return 'border-gray-700 hover:border-gray-500'
  if (isBadPhoto(p)) return 'border-red-500/60 hover:border-red-400'
  const bibs = visibleDets(p).map(d => effectiveBib(d)).filter(Boolean)
  if (bibs.length) return 'border-green-500/60 hover:border-green-400'
  return 'border-amber-500/60 hover:border-amber-400'
})

const currentPhotoSignal = computed(() => {
  const p = currentPhoto.value
  if (!p) return 'none'
  if (isBadPhoto(p)) return 'bad'
  const dets = currentVisibleDets.value
  const bibs = dets.map(d => effectiveBib(d)).filter(Boolean)
  if (bibs.length) return 'good'
  return 'noBib'
})

const progressPct = computed(() => {
  if (!sessionPhotos.value.length) return 0
  return Math.round(verifDoneCount.value / sessionPhotos.value.length * 100)
})

const currentVisibleDets = computed(() => {
  if (showSecondary.value) return allDets(currentPhoto.value)
  return visibleDets(currentPhoto.value)
})

const hiddenDetsCount = computed(() => {
  if (!currentPhoto.value) return 0
  return allDets(currentPhoto.value).length - visibleDets(currentPhoto.value).length
})

const currentVerifStatus = computed(() => currentPhoto.value ? photoVerifStatus(currentPhoto.value) : 'pending')

const verifDoneCount = computed(() => sessionPhotos.value.filter(p => photoVerifStatus(p) !== 'pending').length)

const sessionFilters = computed(() => {
  const all = sessionPhotos.value
  return [
    { key: 'all', label: 'Toutes', count: all.length },
    { key: 'pending', label: 'A traiter', count: all.filter(p => photoVerifStatus(p) === 'pending').length },
    { key: 'validated', label: 'Valides', count: all.filter(p => photoVerifStatus(p) === 'validated').length },
    { key: 'rejected', label: 'Rejetes', count: all.filter(p => photoVerifStatus(p) === 'rejected').length },
  ]
})

const bibPlaceholder = computed(() => {
  const n = currentVisibleDets.value.length
  if (!n) return 'x pour rejeter'
  if (n === 1) return 'N dossard ou x'
  return `${n} dossards (espaces)`
})

const bibInputBorder = computed(() => {
  const s = currentVerifStatus.value
  if (s === 'validated') return 'border-green-600/60'
  if (s === 'rejected') return 'border-red-600/60'
  return 'border-gray-600 focus:border-blue-500'
})

// ============================================================
// HELPERS
// ============================================================

function effectiveBib(det) { return det.validated_bib || det.bib_number }
function effectiveClass(det) { return det.validated_class || det.classification }

function photoUrl(photo) {
  const filename = photo.filepath.split('/').pop()
  return `/uploads/${eventId.value}/${filename}`
}

function cacheBust(photo) {
  return photo._rotated ? '?t=' + photo._rotated : ''
}

function visibleDets(photo) {
  if (!photo?.detections?.length) return []
  const sorted = [...photo.detections].sort((a, b) => (b.main_subject_score || 0) - (a.main_subject_score || 0))
  // Filter out non-usable subjects (advanced filtering) — keep at least one
  const usable = sorted.filter(d => d.is_usable_subject !== false)
  const base = usable.length ? usable : sorted.slice(0, 1)
  if (base.length <= 1) return base
  return base.filter((d, i) => i === 0 || (d.main_subject_score || 0) >= SECONDARY_THRESHOLD)
}

function allDets(photo) {
  if (!photo?.detections?.length) return []
  return [...photo.detections].sort((a, b) => (b.main_subject_score || 0) - (a.main_subject_score || 0))
}

function photoVerifStatus(photo) {
  if (!photo) return 'pending'
  const dets = visibleDets(photo)
  if (!dets.length) return 'pending'
  const allV = dets.every(d => d.validated)
  if (!allV) return 'pending'
  if (dets.some(d => d.validated_class === 'bon')) return 'validated'
  return 'rejected'
}

function photoIndex(photo) {
  const idx = sessionPhotos.value.indexOf(photo)
  return String(idx + 1).padStart(3, '0')
}

function photoBibSummary(photo) {
  const bibs = visibleDets(photo).map(d => effectiveBib(d)).filter(Boolean)
  return bibs.join(' ') || ''
}

function classificationLabel(photo) {
  if (!photo.detections.length) return 'Aucune'
  const classes = photo.detections.map(d => effectiveClass(d))
  if (classes.includes('bon')) return 'Bon'
  if (classes.includes('incertain')) return 'Incertain'
  if (classes.includes('flou')) return 'Flou'
  if (classes.includes('coupe')) return 'Coupe'
  return 'Mauvais'
}

function classificationBadge(photo) {
  const cls = classificationLabel(photo).toLowerCase()
  const map = {
    bon: 'bg-green-100/80 text-green-700',
    mauvais: 'bg-red-100/80 text-red-700',
    flou: 'bg-gray-100/80 text-gray-600',
    coupe: 'bg-red-100/80 text-red-700',
    incertain: 'bg-blue-100/80 text-blue-700',
    aucune: 'bg-red-100/80 text-red-700',
  }
  return map[cls] || 'bg-gray-100/80 text-gray-600'
}

// --- Status visuals ---
function statusDot(s) {
  return {
    validated: 'bg-green-500',
    rejected: 'bg-red-500',
    pending: 'bg-gray-600',
  }[s] || 'bg-gray-600'
}

function statusLabel(s) {
  return { validated: 'Valide', rejected: 'Rejete', pending: 'A traiter' }[s] || ''
}


// ============================================================
// LOAD
// ============================================================

async function loadPhotos() {
  loading.value = true
  try {
    const params = { processed_only: true }
    if (cardId.value) params.card_id = cardId.value
    const res = await photosApi.list(eventId.value, params)
    allPhotos.value = res.data
    if (cardId.value) {
      try {
        const evRes = await import('../../api/events').then(m => m.eventsApi.get(eventId.value))
        const card = evRes.data.cards?.find(c => c.id === Number(cardId.value))
        cardName.value = card?.name || `Carte #${cardId.value}`
      } catch { cardName.value = `Carte #${cardId.value}` }
    }
  } finally {
    loading.value = false
  }
}

// ============================================================
// VIEWER
// ============================================================

function openViewer(idx) {
  verifMode.value = false
  sessionFilter.value = 'all'
  sessionPhotos.value = [...filteredPhotos.value].sort((a, b) => a.id - b.id)
  viewerIdx.value = idx
  history.value = []
  viewerOpen.value = true
  syncBibField()
}

function startVerifMode() {
  if (!allPhotos.value.length) return
  verifMode.value = true
  sessionFilter.value = 'all'
  sessionPhotos.value = [...allPhotos.value].sort((a, b) => a.id - b.id)
  viewerIdx.value = 0
  history.value = []
  viewerOpen.value = true
  syncBibField()
}

function closeViewer() {
  viewerOpen.value = false
  verifMode.value = false
  loadPhotos()
}

function isBadPhoto(photo) {
  if (!photo) return false
  const dets = visibleDets(photo)
  // No detections at all = bad
  if (!dets.length) return true
  // All detections are flou/coupe/mauvais with no bib = bad
  const allBad = dets.every(d => {
    const cls = effectiveClass(d)
    return (cls === 'flou' || cls === 'coupe' || cls === 'mauvais') && !effectiveBib(d)
  })
  return allBad
}

function syncBibField() {
  const photo = currentPhoto.value
  if (!photo) return
  const dets = currentVisibleDets.value

  // Already validated — just show current state
  if (photoVerifStatus(photo) !== 'pending') {
    const bibs = dets.map(d => effectiveBib(d)).filter(Boolean)
    bibFieldValue.value = bibs.length ? bibs.join(' ') : 'x'
    nextTick(() => { bibInput.value?.focus(); bibInput.value?.select() })
    return
  }

  // Bad photo (flou, coupe, no detection) → pre-fill x
  if (isBadPhoto(photo)) {
    bibFieldValue.value = 'x'
    nextTick(() => { bibInput.value?.focus(); bibInput.value?.select() })
    return
  }

  // Person detected with bib → show bibs
  const bibs = dets.map(d => effectiveBib(d)).filter(Boolean)
  if (bibs.length) {
    bibFieldValue.value = bibs.join(' ')
  } else {
    // Person detected but no bib → 90000
    bibFieldValue.value = dets.map(() => '90000').join(' ')
  }

  nextTick(() => {
    bibInput.value?.focus()
    bibInput.value?.select()
  })
}

watch(viewerIdx, syncBibField)
watch(showSecondary, syncBibField)

function goToPhoto(photo) {
  const idx = sessionPhotos.value.findIndex(p => p.id === photo.id)
  if (idx !== -1) viewerIdx.value = idx
}

function goToNextPending() {
  // Go back to where we were working: next pending after last validated photo
  const from = lastValidatedIdx.value >= 0 ? lastValidatedIdx.value : -1
  for (let offset = 1; offset < sessionPhotos.value.length; offset++) {
    const idx = (from + offset) % sessionPhotos.value.length
    if (photoVerifStatus(sessionPhotos.value[idx]) === 'pending') {
      viewerIdx.value = idx
      return
    }
  }
}

function setSessionFilter(key) {
  sessionFilter.value = key
}

function viewerNav(dir) {
  if (!sessionPhotos.value.length) return
  let next = viewerIdx.value + dir
  if (next < 0) next = sessionPhotos.value.length - 1
  if (next >= sessionPhotos.value.length) next = 0
  viewerIdx.value = next
}

// ============================================================
// VALIDATION
// ============================================================

async function validateAndNext() {
  const photo = currentPhoto.value
  if (!photo) return
  const raw = bibFieldValue.value.trim()
  if (!raw) return
  if (raw === 'x' || raw === 'X') { await rejectAndNext(); return }

  const dets = currentVisibleDets.value

  // No detections (unprocessed photo) — skip to next
  if (!dets.length) {
    flash()
    advanceToNextPending()
    return
  }

  const bibs = raw.split(/\s+/).filter(Boolean)
  const prevStates = savePrevStates(dets)

  for (let i = 0; i < dets.length; i++) {
    const det = dets[i]
    const bib = bibs[i] || null
    const body = {}
    if (bib) {
      body.validated_bib = bib
      body.validated_class = 'bon'
    } else {
      body.validated_class = effectiveBib(det) ? 'bon' : 'incertain'
    }
    await photosApi.validateDetection(det.id, body)
    det.validated = true
    if (bib) det.validated_bib = bib
    det.validated_class = body.validated_class
    det.status = body.validated_class === 'bon' ? 'confirmed' : 'manual'
  }

  history.value.push({ photoId: photo.id, prevStates })
  lastValidatedIdx.value = viewerIdx.value
  flash()
  advanceToNextPending()
}

async function rejectAndNext() {
  const photo = currentPhoto.value
  if (!photo) return
  const dets = currentVisibleDets.value

  // No detections (unprocessed photo) — skip to next
  if (!dets.length) {
    flash()
    advanceToNextPending()
    return
  }

  const prevStates = savePrevStates(dets)

  for (const det of dets) {
    await photosApi.validateDetection(det.id, { validated_class: 'mauvais' })
    det.validated = true
    det.validated_class = 'mauvais'
    det.status = 'rejected'
  }

  history.value.push({ photoId: photo.id, prevStates })
  lastValidatedIdx.value = viewerIdx.value
  flash()
  advanceToNextPending()
}

function savePrevStates(dets) {
  return dets.map(d => ({
    id: d.id,
    prevBib: d.validated_bib,
    prevClass: d.validated_class,
    prevValidated: d.validated,
    prevStatus: d.status,
  }))
}

function flash() {
  flashClass.value = 'opacity-30'
  setTimeout(() => { flashClass.value = '' }, 120)
}

function advanceToNextPending() {
  // All done? Auto-close
  if (verifDoneCount.value === sessionPhotos.value.length) {
    toast.success(`Session terminee ! ${sessionPhotos.value.length} photos traitees.`)
    closeViewer()
    return
  }
  // Find next pending photo after current
  for (let offset = 1; offset < sessionPhotos.value.length; offset++) {
    const idx = (viewerIdx.value + offset) % sessionPhotos.value.length
    if (photoVerifStatus(sessionPhotos.value[idx]) === 'pending') {
      viewerIdx.value = idx
      return
    }
  }
  // Shouldn't happen but fallback: move forward one
  if (viewerIdx.value + 1 < sessionPhotos.value.length) {
    viewerIdx.value++
  }
}

async function vUndo() {
  if (!history.value.length) return
  const last = history.value.pop()
  if (!last) return
  const photo = sessionPhotos.value.find(p => p.id === last.photoId)
  if (!photo) return

  for (const prev of last.prevStates) {
    const det = photo.detections.find(d => d.id === prev.id)
    if (!det) continue
    await photosApi.validateDetection(det.id, {
      validated_class: prev.prevClass || null,
      validated_bib: prev.prevBib || null,
    })
    det.validated = prev.prevValidated
    det.validated_class = prev.prevClass
    det.validated_bib = prev.prevBib
    det.status = prev.prevStatus
  }

  const idx = sessionPhotos.value.findIndex(p => p.id === last.photoId)
  if (idx !== -1) viewerIdx.value = idx
}

async function vRotate() {
  if (!currentPhoto.value) return
  const res = await photosApi.rotate(currentPhoto.value.id)
  if (res.data?.width) {
    currentPhoto.value.width = res.data.width
    currentPhoto.value.height = res.data.height
  }
  currentPhoto.value._rotated = Date.now()
}

// ============================================================
// BBOX DRAWING
// ============================================================

function onImgLoad() { nextTick(drawBbox) }

function drawBbox() {
  const canvas = bboxCanvas.value
  const img = viewerImg.value
  const wrap = imgWrap.value
  if (!canvas || !img || !wrap || !currentPhoto.value) return

  const dets = currentVisibleDets.value
  const ir = img.getBoundingClientRect()
  const wr = wrap.getBoundingClientRect()

  canvas.width = img.naturalWidth
  canvas.height = img.naturalHeight
  canvas.style.width = ir.width + 'px'
  canvas.style.height = ir.height + 'px'
  canvas.style.left = (ir.left - wr.left) + 'px'
  canvas.style.top = (ir.top - wr.top) + 'px'

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const p = currentPhoto.value
  const sx = img.naturalWidth / (p.width || img.naturalWidth)
  const sy = img.naturalHeight / (p.height || img.naturalHeight)

  for (let i = 0; i < dets.length; i++) {
    const d = dets[i]
    if (!d.bbox_w) continue

    const bib = effectiveBib(d)
    const cls = effectiveClass(d)
    const isBad = (cls === 'flou' || cls === 'coupe' || cls === 'mauvais')
    const weak = (d.main_subject_score || 0) < SECONDARY_THRESHOLD

    // Semantic colors: green = person + bib, red = no bib / bad quality
    const color = bib && !isBad ? '#34d399' : '#ef4444'

    ctx.strokeStyle = color
    ctx.lineWidth = weak ? 2 : 4
    if (weak) ctx.setLineDash([6, 4])
    else ctx.setLineDash([])
    ctx.strokeRect(d.bbox_x * sx, d.bbox_y * sy, d.bbox_w * sx, d.bbox_h * sy)
    ctx.setLineDash([])

    // Label: bib number or "?" / "FLOU" / "COUPE"
    const fontSize = Math.max(28, canvas.width * 0.035)
    ctx.font = `bold ${fontSize}px sans-serif`
    const labelY = d.bbox_y * sy - 10
    const labelX = d.bbox_x * sx

    if (bib) {
      // Green label with background
      const text = '#' + bib
      const tw = ctx.measureText(text).width
      ctx.fillStyle = 'rgba(16, 185, 129, 0.85)'
      ctx.fillRect(labelX, labelY - fontSize, tw + 12, fontSize + 6)
      ctx.fillStyle = '#fff'
      ctx.fillText(text, labelX + 6, labelY - 4)
    } else {
      // Red label
      const text = isBad ? (cls === 'flou' ? 'FLOU' : cls === 'coupe' ? 'COUPE' : '?') : '?'
      const tw = ctx.measureText(text).width
      ctx.fillStyle = 'rgba(239, 68, 68, 0.85)'
      ctx.fillRect(labelX, labelY - fontSize, tw + 12, fontSize + 6)
      ctx.fillStyle = '#fff'
      ctx.fillText(text, labelX + 6, labelY - 4)
    }
  }
}

watch(showSecondary, () => nextTick(drawBbox))

// ============================================================
// ZOOM
// ============================================================

function onZoomMove(e) {
  const img = viewerImg.value
  const wrap = imgWrap.value
  if (!img || !wrap || !img.naturalWidth) return
  const rect = img.getBoundingClientRect()
  const wrapRect = wrap.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  zoomStyle.value = {
    backgroundImage: `url(${img.src})`,
    backgroundSize: `${img.clientWidth * ZOOM_FACTOR}px ${img.clientHeight * ZOOM_FACTOR}px`,
    left: (rect.left - wrapRect.left) + x - 150 + 'px',
    top: (rect.top - wrapRect.top) + y - 100 + 'px',
    backgroundPosition: `${-(x * ZOOM_FACTOR - 150)}px ${-(y * ZOOM_FACTOR - 100)}px`,
  }
}

// ============================================================
// KEYBOARD
// ============================================================

function handleKey(e) {
  if (!viewerOpen.value) return
  const isInput = document.activeElement === bibInput.value

  // Typing: digits, space, backspace go to bib field
  if (e.key >= '0' && e.key <= '9' || e.key === ' ' || e.key === 'Backspace' || e.key === 'Delete') {
    if (!isInput) {
      e.preventDefault()
      bibInput.value?.focus()
      if (e.key >= '0' && e.key <= '9' || e.key === ' ') {
        bibFieldValue.value += e.key
      } else if (e.key === 'Backspace' && bibFieldValue.value.length) {
        bibFieldValue.value = bibFieldValue.value.slice(0, -1)
      }
    }
    return
  }

  if ((e.key === 'x' || e.key === 'X') && !isInput) {
    e.preventDefault()
    bibFieldValue.value = 'x'
    bibInput.value?.focus()
    return
  }

  if (e.key === 'Enter') {
    if (!isInput) { e.preventDefault(); validateAndNext() }
    return
  }

  e.preventDefault()
  switch (e.key) {
    case 'a': case 'A': rejectAndNext(); break
    case 'z': case 'Z': vUndo(); break
    case 'r': case 'R': vRotate(); break
    case '&': goToNextPending(); break
    case 'ArrowLeft': viewerNav(-1); break
    case 'ArrowRight': viewerNav(1); break
    case 'Escape': closeViewer(); break
  }
}

// ============================================================
// LIFECYCLE
// ============================================================

onMounted(async () => {
  await loadPhotos()
  window.addEventListener('keydown', handleKey)
  if (autoVerif.value && allPhotos.value.length) {
    nextTick(() => startVerifMode())
  }
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKey)
})
</script>
