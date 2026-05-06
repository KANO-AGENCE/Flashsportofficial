<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="px-6 py-4 bg-white/70 backdrop-blur-xl border-b border-white/60 flex items-center gap-4 shrink-0">
      <button @click="router.push(`/tri/events/${route.params.id}`)" class="text-gray-400 hover:text-gray-600 transition">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <h1 class="text-lg font-bold text-gray-900 flex-1">
        Resultats
        <span v-if="cardName" class="text-sm font-normal text-gray-500 ml-2">— {{ cardName }}</span>
      </h1>

      <!-- Filters -->
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

      <button
        @click="startVerifMode"
        class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg shadow-blue-500/25 transition-all hover:shadow-blue-500/40"
      >
        Mode Verification
      </button>
    </div>

    <!-- Photo list (linear) -->
    <div class="flex-1 overflow-y-auto p-6">
      <div v-if="loading" class="text-center py-12 text-gray-400">Chargement...</div>
      <div v-else-if="!filteredPhotos.length" class="text-center py-12 text-gray-400">Aucune photo</div>
      <div v-else class="space-y-3">
        <div
          v-for="(photo, idx) in filteredPhotos"
          :key="photo.id"
          @click="openViewer(idx)"
          class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl shadow-lg shadow-black/5 hover:border-blue-300/60 hover:shadow-blue-500/10 transition-all cursor-pointer flex items-center gap-4 p-3"
        >
          <div class="w-20 h-20 rounded-xl overflow-hidden bg-gray-100/80 shrink-0">
            <img :src="photoUrl(photo)" class="w-full h-full object-cover" loading="lazy">
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <template v-for="det in photo.detections" :key="det.id">
                <span v-if="effectiveBib(det)" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-green-100/80 text-green-700 backdrop-blur-sm">
                  #{{ effectiveBib(det) }}
                </span>
                <span v-else class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-gray-100/80 text-gray-700 backdrop-blur-sm">
                  ?
                </span>
              </template>
              <span v-if="!photo.detections.length" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-red-100/80 text-red-700 backdrop-blur-sm">
                Mauvais
              </span>
            </div>
            <p class="text-sm text-gray-500 truncate">{{ photo.filename }}</p>
          </div>
          <div class="flex items-center gap-1.5 shrink-0">
            <span v-if="photo.detections?.[0]?.fallback_used" class="text-xs px-1.5 py-0.5 rounded bg-amber-100/80 text-amber-700 backdrop-blur-sm" title="Fallback Qwen utilise">FB</span>
            <span v-if="photo.processing_time" class="text-xs text-gray-400">{{ photo.processing_time.toFixed(1) }}s</span>
            <span :class="classificationBadge(photo)" class="text-xs font-medium px-2.5 py-1 rounded-full backdrop-blur-sm">
              {{ classificationLabel(photo) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== VIEWER MODAL ========== -->
    <div v-if="viewerOpen" class="fixed inset-0 bg-black z-50 flex flex-col" tabindex="0" ref="viewerEl">

      <!-- Verif progress bar -->
      <div v-if="verifMode" class="bg-gray-900 px-4 py-2 shrink-0">
        <div class="flex items-center gap-4 mb-1">
          <span class="text-xs text-gray-400">Photo {{ viewerIdx + 1 }}/{{ viewerPhotos.length }}</span>
          <div class="flex-1"></div>
          <span class="text-xs text-gray-400">{{ verifDone }}/{{ verifTotal }} verifiees</span>
        </div>
        <div class="w-full bg-gray-800 rounded-full h-1">
          <div class="bg-blue-500 h-1 rounded-full transition-all" :style="{ width: verifProgressPct + '%' }"></div>
        </div>
      </div>

      <!-- Top bar -->
      <div class="flex items-center justify-between px-4 py-3 bg-black/80 text-white shrink-0">
        <button @click="closeViewer" class="hover:text-gray-300">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>

        <!-- Title -->
        <div class="text-center flex-1">
          <span v-if="currentDetection" :class="classificationBadge(currentPhoto)" class="text-xs font-bold px-2 py-0.5 rounded mr-2">
            {{ currentDetection.classification }}
          </span>
          <span v-if="currentDetection && effectiveBib(currentDetection)" class="text-sm">
            #{{ effectiveBib(currentDetection) }}
          </span>
        </div>

        <span class="text-sm text-gray-400">{{ viewerIdx + 1 }}/{{ viewerPhotos.length }}</span>

        <div class="flex items-center gap-2 ml-4">
          <span v-for="det in (currentPhoto?.detections || [])" :key="det.id" class="text-sm">
            <span v-if="effectiveBib(det)" class="bg-green-600 px-2 py-1 rounded text-xs font-bold">#{{ effectiveBib(det) }}</span>
            <span v-else class="bg-gray-600 px-2 py-1 rounded text-xs font-bold">?</span>
          </span>
        </div>
      </div>

      <!-- Image + bbox + zoom -->
      <div class="flex-1 flex items-center justify-center relative overflow-hidden" ref="imgWrap">
        <img
          v-if="currentPhoto"
          ref="viewerImg"
          :src="photoUrl(currentPhoto) + (currentPhoto._rotated ? '?t=' + currentPhoto._rotated : '')"
          :class="['max-w-full max-h-full object-contain transition-opacity', flashClass]"
          @load="onImgLoad"
          @mouseenter="zoomActive = true"
          @mouseleave="zoomActive = false"
          @mousemove="onZoomMove"
        >
        <canvas ref="bboxCanvas" class="absolute pointer-events-none"></canvas>

        <!-- Zoom lens -->
        <div
          v-show="zoomActive"
          ref="zoomLens"
          class="absolute pointer-events-none border-2 border-white/50 rounded-lg"
          :style="{ width: '280px', height: '180px', ...zoomStyle }"
        ></div>

        <!-- Nav arrows -->
        <button @click="viewerNav(-1)" class="absolute left-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <button @click="viewerNav(1)" class="absolute right-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full p-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </button>
      </div>

      <!-- Bottom bar -->
      <div class="px-4 py-3 bg-black/80 text-white shrink-0">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-sm text-gray-400">{{ currentDetection?.overall_score != null ? `Score: ${Math.round(currentDetection.overall_score * 100)}/100` : '' }}</span>
          <span :class="['text-xs font-medium px-2 py-0.5 rounded', badgeClassForDet]">{{ effectiveClassLabel }}</span>
          <span class="flex-1"></span>
          <span class="text-xs text-gray-500">{{ currentPhoto?.filename }}</span>
        </div>
        <div class="flex items-center gap-2">
          <button @click="vAct('bon')" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium transition">Entree Bon</button>
          <button @click="vAct('mauvais')" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-sm font-medium transition">A Mauvais</button>
          <button @click="vUndo" :disabled="!history.length" class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-30">Z Annuler</button>
          <button @click="vRotate" class="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium transition">R Rotation</button>
          <button @click="viewerNav(-1)" class="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg text-sm transition">←</button>
          <button @click="viewerNav(1)" class="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg text-sm transition">→</button>
          <div class="flex-1"></div>
          <input
            ref="bibInput"
            v-model="viewerBibValue"
            type="text"
            placeholder="N dossard"
            class="bg-gray-800 border border-gray-600 text-white px-3 py-2 rounded-lg text-sm w-28"
            @keydown.enter.prevent="assignBibAndValidate"
          >
          <span class="text-xs text-gray-600 hidden md:block">Entrer=Bon A=Mauvais Z=Annuler R=Rotation</span>
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

// --- Refs ---
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

// --- Viewer ---
const viewerOpen = ref(false)
const viewerPhotos = ref([])
const viewerIdx = ref(0)
const viewerBibValue = ref('')
const history = ref([])
const flashClass = ref('')

// --- Zoom ---
const zoomActive = ref(false)
const zoomStyle = ref({})
const ZOOM_FACTOR = 3
const ZOOM_W = 280
const ZOOM_H = 180

// --- Verif mode ---
const verifMode = ref(false)
const verifTotal = ref(0)
const verifDone = ref(0)

const eventId = computed(() => route.params.id)
const cardId = computed(() => route.query.card_id || null)
const autoVerif = computed(() => route.query.verif === '1')
const cardName = ref('')

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

const currentPhoto = computed(() => viewerPhotos.value[viewerIdx.value] || null)
const currentDetection = computed(() => currentPhoto.value?.detections?.[0] || null)
const verifProgressPct = computed(() => {
  if (!verifTotal.value) return 0
  return Math.round(verifDone.value / verifTotal.value * 100)
})

const effectiveClassLabel = computed(() => {
  if (!currentDetection.value) return 'Mauvais'
  return effectiveClass(currentDetection.value)
})

const badgeClassForDet = computed(() => {
  const cls = effectiveClassLabel.value?.toLowerCase()
  const map = { bon: 'bg-green-600', mauvais: 'bg-red-600', flou: 'bg-gray-600', coupe: 'bg-red-600', incertain: 'bg-blue-600' }
  return map[cls] || 'bg-gray-600'
})

// --- Helpers ---
function effectiveBib(det) { return det.validated_bib || det.bib_number }
function effectiveClass(det) { return det.validated_class || det.classification }

function photoUrl(photo) {
  const filename = photo.filepath.split('/').pop()
  return `/uploads/${eventId.value}/${filename}`
}

function classificationLabel(photo) {
  if (!photo.detections.length) return 'Mauvais'
  return effectiveClass(photo.detections[0])
}

function classificationBadge(photo) {
  const cls = classificationLabel(photo).toLowerCase()
  const map = {
    bon: 'bg-green-100/80 text-green-700',
    mauvais: 'bg-red-100/80 text-red-700',
    flou: 'bg-gray-100/80 text-gray-600',
    coupe: 'bg-red-100/80 text-red-700',
    incertain: 'bg-blue-100/80 text-blue-700',
  }
  return map[cls] || 'bg-gray-100/80 text-gray-600'
}

// --- Load ---
async function loadPhotos() {
  loading.value = true
  try {
    const params = { processed_only: true }
    if (cardId.value) params.card_id = cardId.value
    const res = await photosApi.list(eventId.value, params)
    allPhotos.value = res.data

    // Load card name if filtering by card
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

// --- Viewer ---
function openViewer(idx) {
  verifMode.value = false
  viewerPhotos.value = [...filteredPhotos.value]
  viewerIdx.value = idx
  history.value = []
  viewerOpen.value = true
  syncBibInput()
}

function closeViewer() {
  viewerOpen.value = false
  verifMode.value = false
  loadPhotos() // refresh list
}

function syncBibInput() {
  const det = currentDetection.value
  if (!det) {
    viewerBibValue.value = 'x'
  } else {
    const cls = det.classification
    // Coupé/mauvais/flou = toujours "x", même si un bib a été détecté
    if (cls === 'mauvais' || cls === 'coupe' || cls === 'flou') {
      viewerBibValue.value = 'x'
    } else {
      const bib = effectiveBib(det)
      viewerBibValue.value = bib || ''
    }
  }
  nextTick(() => {
    bibInput.value?.focus()
    bibInput.value?.select()
  })
}

watch(viewerIdx, syncBibInput)

function viewerNav(dir) {
  if (!viewerPhotos.value.length) return
  viewerIdx.value += dir
  if (viewerIdx.value < 0) viewerIdx.value = viewerPhotos.value.length - 1
  if (viewerIdx.value >= viewerPhotos.value.length) viewerIdx.value = 0
}

async function vAct(cls) {
  if (!viewerPhotos.value.length) return
  const p = viewerPhotos.value[viewerIdx.value]
  const d = p.detections?.[0]
  if (!d) {
    viewerPhotos.value.splice(viewerIdx.value, 1)
    if (!viewerPhotos.value.length) { closeViewer(); return }
    if (viewerIdx.value >= viewerPhotos.value.length) viewerIdx.value = 0
    syncBibInput()
    return
  }

  const body = { validated_class: cls }
  const bibVal = viewerBibValue.value.trim()
  if (bibVal) body.validated_bib = bibVal

  const prevClass = d.validated_class || d.classification
  const prevBib = d.validated_bib || d.bib_number

  await photosApi.validateDetection(d.id, body)
  d.validated = true
  d.validated_class = cls
  if (bibVal) d.validated_bib = bibVal

  history.value.push({ photo: p, index: viewerIdx.value, prevClass, prevBib })
  viewerPhotos.value.splice(viewerIdx.value, 1)

  if (verifMode.value) verifDone.value++

  // Flash
  flashClass.value = 'opacity-30'
  setTimeout(() => { flashClass.value = '' }, 200)

  setTimeout(() => {
    if (!viewerPhotos.value.length) {
      closeViewer()
      return
    }
    if (viewerIdx.value >= viewerPhotos.value.length) viewerIdx.value = 0
    // Sync bib input for the new current photo (watch doesn't fire if index unchanged after splice)
    syncBibInput()
  }, 150)
}

async function vUndo() {
  if (!history.value.length) return
  const last = history.value.pop()
  const d = last.photo.detections?.[0]
  if (!d) return
  await photosApi.validateDetection(d.id, { validated_class: last.prevClass, validated_bib: last.prevBib || null })
  d.validated_class = last.prevClass
  d.validated_bib = last.prevBib
  viewerPhotos.value.splice(last.index, 0, last.photo)
  viewerIdx.value = last.index
  if (verifMode.value) verifDone.value = Math.max(0, verifDone.value - 1)
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

function assignBibAndValidate() {
  const val = viewerBibValue.value.trim()
  if (!val) return // must have a bib or "x"
  if (val === 'x') {
    vAct('mauvais')
  } else {
    vAct('bon')
  }
}

// --- Verif Mode ---
function startVerifMode() {
  if (!allPhotos.value.length) return

  // All photos not yet validated, in card order (by id = import order)
  const queue = allPhotos.value
    .filter(p => {
      const d = p.detections?.[0]
      return !d || !d.validated_class
    })
    .sort((a, b) => a.id - b.id)

  if (!queue.length) {
    toast.info('Rien a verifier ! Toutes les photos sont deja traitees.')
    return
  }

  verifMode.value = true
  viewerPhotos.value = queue
  verifTotal.value = queue.length
  verifDone.value = 0
  viewerIdx.value = 0
  history.value = []
  viewerOpen.value = true
  syncBibInput()
}

// --- Bbox drawing ---
function onImgLoad() {
  drawBbox()
}

function drawBbox() {
  const canvas = bboxCanvas.value
  const img = viewerImg.value
  const wrap = imgWrap.value
  if (!canvas || !img || !wrap || !currentPhoto.value) return

  const d = currentDetection.value
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

  if (!d || !d.bbox_w) return

  const p = currentPhoto.value
  const sx = img.naturalWidth / (p.width || img.naturalWidth)
  const sy = img.naturalHeight / (p.height || img.naturalHeight)

  const cls = effectiveClass(d)
  ctx.strokeStyle = cls === 'bon' ? '#34d399' : cls === 'incertain' ? '#60a5fa' : '#f87171'
  ctx.lineWidth = 4
  ctx.strokeRect(d.bbox_x * sx, d.bbox_y * sy, d.bbox_w * sx, d.bbox_h * sy)

  const bibT = effectiveBib(d)
  if (bibT) {
    ctx.fillStyle = ctx.strokeStyle
    ctx.font = `bold ${Math.max(28, canvas.width * 0.035)}px sans-serif`
    ctx.fillText('#' + bibT, d.bbox_x * sx, d.bbox_y * sy - 10)
  }
}

// --- Zoom ---
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
    left: (rect.left - wrapRect.left) + x - ZOOM_W / 2 + 'px',
    top: (rect.top - wrapRect.top) + y - ZOOM_H / 2 + 'px',
    backgroundPosition: `${-(x * ZOOM_FACTOR - ZOOM_W / 2)}px ${-(y * ZOOM_FACTOR - ZOOM_H / 2)}px`,
  }
}

// --- Keyboard ---
function handleKey(e) {
  if (!viewerOpen.value) return

  // Digits + space + x: type in bib field (space for multi-bib like "123 456", x for rejected)
  if (e.key >= '0' && e.key <= '9' || e.key === ' ' || e.key === 'x' || e.key === 'X') {
    e.preventDefault()
    if (bibInput.value && bibInput.value.selectionStart !== bibInput.value.selectionEnd) {
      viewerBibValue.value = ''
    }
    viewerBibValue.value += e.key
    nextTick(() => bibInput.value?.focus())
    return
  }
  if (e.key === 'Backspace' || e.key === 'Delete') {
    e.preventDefault()
    if (viewerBibValue.value.length > 0) {
      viewerBibValue.value = viewerBibValue.value.slice(0, -1)
    }
    return
  }

  e.preventDefault()

  switch (e.key) {
    case 'Enter': assignBibAndValidate(); break
    case 'a': case 'A': viewerBibValue.value = 'x'; vAct('mauvais'); break
    case 'z': case 'Z': vUndo(); break
    case 'r': case 'R': vRotate(); break
    case 'ArrowLeft': viewerNav(-1); return
    case 'ArrowRight': viewerNav(1); return
    case 'Escape': closeViewer(); return
  }

  // After action (not nav), re-focus and select bib input
  nextTick(() => {
    bibInput.value?.focus()
    bibInput.value?.select()
  })
}

onMounted(async () => {
  await loadPhotos()
  window.addEventListener('keydown', handleKey)
  // Auto-start verif mode if requested via query param
  if (autoVerif.value && allPhotos.value.length) {
    nextTick(() => startVerifMode())
  }
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKey)
})
</script>
