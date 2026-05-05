<template>
  <div class="p-8 max-w-6xl mx-auto space-y-8">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Outils TRI</h1>
        <p class="text-slate-500 text-sm mt-1">Course #{{ eventId }} — Participants, cadres, exports</p>
      </div>
      <router-link :to="`/tri/events/${eventId}`" class="px-4 py-2 text-sm text-slate-600 bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl hover:bg-white/90 transition">
        Retour
      </router-link>
    </div>

    <!-- Participants Section -->
    <section class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        Participants
      </h2>

      <div class="flex items-center gap-4 mb-4">
        <label class="flex-1">
          <div class="flex items-center gap-3 px-4 py-3 bg-white/50 border border-white/40 rounded-xl cursor-pointer hover:bg-white/70 transition">
            <svg class="w-5 h-5 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
            <span class="text-sm text-slate-600">{{ participantFile ? participantFile.name : 'Importer un fichier Excel (.xlsx)' }}</span>
            <input type="file" accept=".xlsx,.xls" class="hidden" @change="onParticipantFileChange">
          </div>
        </label>
        <button
          @click="importParticipants"
          :disabled="!participantFile || importingParticipants"
          class="px-5 py-3 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          {{ importingParticipants ? 'Import...' : 'Importer' }}
        </button>
      </div>

      <div v-if="importResult" class="px-4 py-3 rounded-xl text-sm mb-4" :class="importResult.errors?.length ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'">
        {{ importResult.imported }} importes, {{ importResult.skipped }} ignores
        <span v-if="importResult.errors?.length"> — {{ importResult.errors.length }} erreur(s)</span>
      </div>

      <div v-if="participants.length" class="text-sm text-slate-500 mb-2">{{ participants.length }} participants</div>
      <div v-if="participants.length" class="max-h-60 overflow-y-auto rounded-xl border border-white/40">
        <table class="w-full text-sm">
          <thead class="bg-white/60 sticky top-0">
            <tr>
              <th class="text-left px-3 py-2 text-slate-500 font-medium">Dossard</th>
              <th class="text-left px-3 py-2 text-slate-500 font-medium">Nom</th>
              <th class="text-left px-3 py-2 text-slate-500 font-medium">Prenom</th>
              <th class="text-left px-3 py-2 text-slate-500 font-medium">Temps</th>
              <th class="text-left px-3 py-2 text-slate-500 font-medium">Pays</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in participants" :key="p.id" class="border-t border-white/30 hover:bg-white/40">
              <td class="px-3 py-2 font-mono font-medium text-blue-600">{{ p.bib_number }}</td>
              <td class="px-3 py-2 text-slate-700">{{ p.last_name || '—' }}</td>
              <td class="px-3 py-2 text-slate-700">{{ p.first_name || '—' }}</td>
              <td class="px-3 py-2 text-slate-600">{{ p.race_time || '—' }}</td>
              <td class="px-3 py-2 text-slate-600">{{ p.country || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Cadres / Frames Section -->
    <section class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
        Cadres decoratifs
      </h2>

      <!-- Upload new frame -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <label class="col-span-2">
          <div class="flex items-center gap-3 px-4 py-3 bg-white/50 border border-white/40 rounded-xl cursor-pointer hover:bg-white/70 transition">
            <svg class="w-5 h-5 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            <span class="text-sm text-slate-600">{{ frameFile ? frameFile.name : 'Choisir un cadre PNG (avec transparence)' }}</span>
            <input type="file" accept="image/png,image/webp" class="hidden" @change="e => frameFile = e.target.files[0]">
          </div>
        </label>
        <input v-model="newFrame.name" placeholder="Nom du cadre" class="px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
        <input v-model="newFrame.text_color" type="color" class="w-12 h-10 rounded-xl border border-white/40 cursor-pointer" title="Couleur du texte">
        <div class="flex items-center gap-2">
          <label class="text-xs text-slate-500 w-16">Pos. X</label>
          <input v-model.number="newFrame.text_x" type="range" min="0" max="1" step="0.01" class="flex-1">
          <span class="text-xs text-slate-400 w-10 text-right">{{ Math.round(newFrame.text_x * 100) }}%</span>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-slate-500 w-16">Pos. Y</label>
          <input v-model.number="newFrame.text_y" type="range" min="0" max="1" step="0.01" class="flex-1">
          <span class="text-xs text-slate-400 w-10 text-right">{{ Math.round(newFrame.text_y * 100) }}%</span>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-slate-500 w-16">Taille</label>
          <input v-model.number="newFrame.text_size" type="range" min="12" max="120" step="1" class="flex-1">
          <span class="text-xs text-slate-400 w-10 text-right">{{ newFrame.text_size }}px</span>
        </div>
        <button
          @click="uploadFrame"
          :disabled="!frameFile || uploadingFrame"
          class="px-5 py-2 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          {{ uploadingFrame ? 'Upload...' : 'Ajouter le cadre' }}
        </button>
      </div>

      <!-- Existing frames -->
      <div v-if="frames.length" class="space-y-3">
        <div v-for="frame in frames" :key="frame.id" class="flex items-center justify-between px-4 py-3 bg-white/50 border border-white/40 rounded-xl">
          <div>
            <span class="font-medium text-slate-700">{{ frame.name }}</span>
            <span class="text-xs text-slate-400 ml-2">Texte: {{ Math.round(frame.text_x * 100) }}% x {{ Math.round(frame.text_y * 100) }}%, {{ frame.text_size }}px</span>
          </div>
          <button @click="deleteFrame(frame.id)" class="text-red-400 hover:text-red-600 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      </div>
      <p v-else class="text-sm text-slate-400">Aucun cadre configure</p>
    </section>

    <!-- Pack & Export Section -->
    <section class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        Packs & Exports
      </h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Download pack -->
        <div class="space-y-3">
          <h3 class="text-sm font-medium text-slate-700">Telecharger un pack (ZIP)</h3>
          <div class="flex gap-2">
            <input v-model="packBib" placeholder="N° dossard" class="flex-1 px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
            <button @click="downloadPack" :disabled="!packBib || downloading" class="px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600 disabled:opacity-40 transition">
              {{ downloading ? '...' : 'ZIP' }}
            </button>
          </div>
        </div>

        <!-- Framed pack -->
        <div class="space-y-3">
          <h3 class="text-sm font-medium text-slate-700">Pack avec cadre</h3>
          <div class="flex gap-2">
            <input v-model="framedBib" placeholder="N° dossard" class="flex-1 px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
            <select v-model="selectedFrameId" class="px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
              <option value="">Cadre...</option>
              <option v-for="f in frames" :key="f.id" :value="f.id">{{ f.name }}</option>
            </select>
            <button @click="downloadFramedPack" :disabled="!framedBib || !selectedFrameId || downloadingFramed" class="px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600 disabled:opacity-40 transition">
              {{ downloadingFramed ? '...' : 'ZIP' }}
            </button>
          </div>
        </div>

        <!-- CSV exports -->
        <div class="space-y-3">
          <h3 class="text-sm font-medium text-slate-700">Export CSV</h3>
          <div class="flex gap-2">
            <button @click="exportPhotosPerBib" class="flex-1 px-4 py-2.5 bg-white/50 border border-white/40 rounded-xl text-sm text-slate-700 hover:bg-white/80 transition">
              Photos par dossard
            </button>
            <button @click="exportPhotoCount" class="flex-1 px-4 py-2.5 bg-white/50 border border-white/40 rounded-xl text-sm text-slate-700 hover:bg-white/80 transition">
              Nombre de photos
            </button>
          </div>
        </div>

        <!-- RGPD delete -->
        <div class="space-y-3">
          <h3 class="text-sm font-medium text-slate-700">Suppression RGPD</h3>
          <div class="flex gap-2">
            <input v-model="rgpdBib" placeholder="N° dossard" class="flex-1 px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-300">
            <button @click="confirmRgpdDelete" :disabled="!rgpdBib || deletingRgpd" class="px-4 py-2 bg-red-500 text-white text-sm rounded-xl hover:bg-red-600 disabled:opacity-40 transition">
              {{ deletingRgpd ? '...' : 'Supprimer' }}
            </button>
          </div>
          <div v-if="rgpdResult" class="px-3 py-2 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
            Dossard {{ rgpdResult.bib_number }} : {{ rgpdResult.web_photos_removed }} web, {{ rgpdResult.detections_removed }} detections, {{ rgpdResult.files_deleted }} fichiers supprimes
          </div>
        </div>
      </div>
    </section>

    <!-- RGPD Confirmation Modal -->
    <div v-if="showRgpdModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div class="bg-white/90 backdrop-blur-xl border border-white/60 shadow-2xl rounded-2xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold text-slate-800 mb-2">Confirmer la suppression RGPD</h3>
        <p class="text-sm text-slate-600 mb-4">
          Cette action est <strong>irreversible</strong>. Toutes les photos du dossard <strong>{{ rgpdBib }}</strong> seront supprimees du site web et du serveur.
        </p>
        <div class="flex justify-end gap-3">
          <button @click="showRgpdModal = false" class="px-4 py-2 text-sm text-slate-600 bg-white/70 border border-white/60 rounded-xl hover:bg-white/90 transition">Annuler</button>
          <button @click="executeRgpdDelete" class="px-4 py-2 text-sm text-white bg-red-500 rounded-xl hover:bg-red-600 transition">Confirmer la suppression</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { triToolsApi } from '../../api/events'

const route = useRoute()
const eventId = route.params.id

// Participants
const participantFile = ref(null)
const importingParticipants = ref(false)
const importResult = ref(null)
const participants = ref([])

// Frames
const frameFile = ref(null)
const uploadingFrame = ref(false)
const frames = ref([])
const newFrame = ref({
  name: 'Cadre',
  text_x: 0.5,
  text_y: 0.9,
  text_size: 48,
  text_color: '#FFFFFF',
})

// Pack / export
const packBib = ref('')
const framedBib = ref('')
const selectedFrameId = ref('')
const downloading = ref(false)
const downloadingFramed = ref(false)

// RGPD
const rgpdBib = ref('')
const deletingRgpd = ref(false)
const rgpdResult = ref(null)
const showRgpdModal = ref(false)

onMounted(async () => {
  await Promise.all([loadParticipants(), loadFrames()])
})

function onParticipantFileChange(e) {
  participantFile.value = e.target.files[0]
  importResult.value = null
}

async function importParticipants() {
  if (!participantFile.value) return
  importingParticipants.value = true
  try {
    const { data } = await triToolsApi.importParticipants(eventId, participantFile.value)
    importResult.value = data
    participantFile.value = null
    await loadParticipants()
  } catch (e) {
    importResult.value = { imported: 0, skipped: 0, errors: [e.response?.data?.detail || 'Erreur'] }
  } finally {
    importingParticipants.value = false
  }
}

async function loadParticipants() {
  try {
    const { data } = await triToolsApi.listParticipants(eventId)
    participants.value = data
  } catch { /* ignore */ }
}

async function loadFrames() {
  try {
    const { data } = await triToolsApi.listFrames(eventId)
    frames.value = data
  } catch { /* ignore */ }
}

async function uploadFrame() {
  if (!frameFile.value) return
  uploadingFrame.value = true
  try {
    await triToolsApi.createFrame(eventId, frameFile.value, newFrame.value)
    frameFile.value = null
    newFrame.value = { name: 'Cadre', text_x: 0.5, text_y: 0.9, text_size: 48, text_color: '#FFFFFF' }
    await loadFrames()
  } catch { /* ignore */ }
  uploadingFrame.value = false
}

async function deleteFrame(frameId) {
  try {
    await triToolsApi.deleteFrame(eventId, frameId)
    await loadFrames()
  } catch { /* ignore */ }
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function downloadPack() {
  downloading.value = true
  try {
    const { data } = await triToolsApi.downloadPack(eventId, packBib.value)
    triggerDownload(data, `pack_${packBib.value}.zip`)
  } catch { /* ignore */ }
  downloading.value = false
}

async function downloadFramedPack() {
  downloadingFramed.value = true
  try {
    const { data } = await triToolsApi.generateFramedPack(eventId, selectedFrameId.value, framedBib.value)
    triggerDownload(data, `pack_cadre_${framedBib.value}.zip`)
  } catch { /* ignore */ }
  downloadingFramed.value = false
}

async function exportPhotosPerBib() {
  try {
    const { data } = await triToolsApi.exportPhotosPerBib(eventId)
    triggerDownload(data, `photos_par_dossard_${eventId}.csv`)
  } catch { /* ignore */ }
}

async function exportPhotoCount() {
  try {
    const { data } = await triToolsApi.exportPhotoCount(eventId)
    triggerDownload(data, `nombre_photos_${eventId}.csv`)
  } catch { /* ignore */ }
}

function confirmRgpdDelete() {
  if (!rgpdBib.value) return
  showRgpdModal.value = true
}

async function executeRgpdDelete() {
  showRgpdModal.value = false
  deletingRgpd.value = true
  try {
    const { data } = await triToolsApi.rgpdDelete(eventId, rgpdBib.value)
    rgpdResult.value = data
  } catch (e) {
    rgpdResult.value = { bib_number: rgpdBib.value, web_photos_removed: 0, detections_removed: 0, files_deleted: 0 }
  }
  deletingRgpd.value = false
}
</script>
