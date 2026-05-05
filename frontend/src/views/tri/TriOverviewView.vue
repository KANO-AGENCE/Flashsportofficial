<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Vue d'ensemble</h1>
        <p class="text-gray-500 text-sm">Supervision centralisee du tri sur tous les postes</p>
      </div>
      <button @click="loadData" class="text-gray-400 hover:text-gray-600 hover:bg-white/50 p-2 rounded-xl transition" title="Rafraichir">
        <svg class="w-5 h-5" :class="loading && 'animate-spin'" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
      </button>
    </div>

    <!-- Global stats -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Courses</p>
        <p class="text-2xl font-bold text-gray-900 mt-1">{{ global.total_events }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4">
        <p class="text-xs text-gray-400 uppercase tracking-wider">En cours</p>
        <p class="text-2xl font-bold text-blue-500 mt-1">{{ global.active_events }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Photos</p>
        <p class="text-2xl font-bold text-gray-900 mt-1">{{ global.total_photos }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Traitees</p>
        <p class="text-2xl font-bold text-blue-600 mt-1">{{ global.total_processed }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Validees</p>
        <p class="text-2xl font-bold text-green-600 mt-1">{{ global.total_validated }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-4">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Dossards</p>
        <p class="text-2xl font-bold text-gray-600 mt-1">{{ global.total_bibs }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && !events.length" class="text-center py-12 text-gray-400">Chargement...</div>

    <!-- Events -->
    <div v-for="ev in events" :key="ev.id" class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl mb-6 overflow-hidden">
      <!-- Event header -->
      <div class="px-5 py-4 border-b border-gray-100/60 flex items-center justify-between bg-white/30">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 backdrop-blur-sm"
            :class="ev.pending > 0 ? 'bg-blue-100/80' : 'bg-green-100/80'">
            <svg v-if="ev.pending > 0" class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <svg v-else class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">{{ ev.name }}</h3>
            <p class="text-xs text-gray-400">{{ formatDate(ev.date) }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button v-if="ev.pending > 0" @click="processEvent(ev.id)" class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-xl text-xs font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">
            Traiter tout
          </button>
          <button v-if="ev.pending > 0" @click="stopEvent(ev.id)" class="bg-red-500 hover:bg-red-400 text-white px-3 py-1.5 rounded-xl text-xs font-medium shadow-lg shadow-red-500/25 transition-all">
            Stop
          </button>
          <router-link :to="`/tri/events/${ev.id}`" class="text-blue-600 hover:text-blue-500 text-xs font-medium px-3 py-1.5 border border-blue-200/60 rounded-xl hover:bg-blue-50/50 transition">
            Ouvrir
          </router-link>
        </div>
      </div>

      <!-- Event stats bar -->
      <div class="px-5 py-3 border-b border-gray-100/60">
        <div class="flex flex-wrap gap-x-6 gap-y-1 text-xs">
          <span class="text-gray-500">{{ ev.total_photos }} photos</span>
          <span class="text-blue-600">{{ ev.processed }} traitees</span>
          <span v-if="ev.pending > 0" class="text-gray-500">{{ ev.pending }} en attente</span>
          <span class="text-green-600">{{ ev.stats.validated }} validees</span>
          <span class="text-gray-600">{{ ev.stats.unique_bibs }} dossards</span>
          <span v-if="ev.stats.validation_pct > 0" class="text-gray-500">{{ ev.stats.validation_pct }}% valide</span>
        </div>
        <!-- Progress bar -->
        <div v-if="ev.total_photos > 0" class="mt-2 flex gap-1 items-center">
          <div class="flex-1 bg-gray-200/50 rounded-full h-2 overflow-hidden">
            <div class="h-full rounded-full transition-all bg-gradient-to-r" :style="{ width: (ev.processed / ev.total_photos * 100) + '%' }"
              :class="ev.pending === 0 ? 'from-green-500 to-green-400' : 'from-blue-500 to-blue-400'"></div>
          </div>
          <span class="text-xs text-gray-400 shrink-0 w-12 text-right">{{ Math.round(ev.processed / ev.total_photos * 100) }}%</span>
        </div>
        <!-- Classification breakdown -->
        <div v-if="ev.stats.total_detections > 0" class="mt-2 flex gap-1 h-1.5 rounded-full overflow-hidden">
          <div v-if="ev.stats.bon" class="bg-green-400" :style="{ width: (ev.stats.bon / ev.stats.total_detections * 100) + '%' }" :title="`Bon: ${ev.stats.bon}`"></div>
          <div v-if="ev.stats.incertain" class="bg-blue-400" :style="{ width: (ev.stats.incertain / ev.stats.total_detections * 100) + '%' }" :title="`Incertain: ${ev.stats.incertain}`"></div>
          <div v-if="ev.stats.flou" class="bg-gray-400" :style="{ width: (ev.stats.flou / ev.stats.total_detections * 100) + '%' }" :title="`Flou: ${ev.stats.flou}`"></div>
          <div v-if="ev.stats.coupe" class="bg-red-400" :style="{ width: (ev.stats.coupe / ev.stats.total_detections * 100) + '%' }" :title="`Coupe: ${ev.stats.coupe}`"></div>
          <div v-if="ev.stats.mauvais" class="bg-gray-400" :style="{ width: (ev.stats.mauvais / ev.stats.total_detections * 100) + '%' }" :title="`Mauvais: ${ev.stats.mauvais}`"></div>
        </div>
      </div>

      <!-- Cards table -->
      <div class="divide-y divide-gray-100/60">
        <div
          v-for="card in ev.cards"
          :key="card.id"
          class="px-5 py-3 flex items-center gap-4 hover:bg-white/30 transition"
          :class="card.locked && 'opacity-50'"
        >
          <!-- Status icon -->
          <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 backdrop-blur-sm"
            :class="cardStatusBg(card)">
            <svg v-if="getCardState(card) === 'locked'" class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            <svg v-else-if="getCardState(card) === 'importing'" class="w-4 h-4 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            <svg v-else-if="getCardState(card) === 'done'" class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            <svg v-else class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
          </div>

          <!-- Card info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h4 class="font-medium text-gray-900 text-sm truncate">{{ card.name }}</h4>
              <span v-if="getCardState(card) === 'locked'" class="text-xs bg-gray-100/80 text-gray-600 px-2 py-0.5 rounded-full backdrop-blur-sm">Gele</span>
              <span v-else-if="getCardState(card) === 'importing'" class="text-xs bg-blue-100/80 text-blue-700 px-2 py-0.5 rounded-full backdrop-blur-sm">Import...</span>
              <span v-else-if="getCardState(card) === 'done'" class="text-xs bg-green-100/80 text-green-700 px-2 py-0.5 rounded-full backdrop-blur-sm">Termine</span>
              <span v-else-if="getCardState(card) === 'error'" class="text-xs bg-red-100/80 text-red-700 px-2 py-0.5 rounded-full backdrop-blur-sm">Erreur</span>
            </div>
            <p class="text-xs text-gray-400">
              {{ card.photo_count }} photos
              <span v-if="card.total_expected"> / {{ card.total_expected }} attendues</span>
            </p>
          </div>

          <!-- Card stats -->
          <div class="flex items-center gap-4 text-xs text-gray-500 shrink-0">
            <div class="text-center">
              <p class="font-semibold text-blue-600">{{ card.processed }}</p>
              <p>traitees</p>
            </div>
            <div class="text-center">
              <p class="font-semibold text-green-600">{{ card.validated }}</p>
              <p>validees</p>
            </div>
            <div class="text-center">
              <p class="font-semibold text-gray-600">{{ card.indexed_bibs }}</p>
              <p>dossards</p>
            </div>
          </div>

          <!-- Card progress -->
          <div class="w-24 shrink-0">
            <div class="bg-gray-200/50 rounded-full h-1.5 overflow-hidden">
              <div class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all"
                :style="{ width: card.photo_count ? (card.processed / card.photo_count * 100) + '%' : '0%' }"></div>
            </div>
          </div>

          <!-- Card actions -->
          <div class="flex items-center gap-1 shrink-0">
            <button v-if="!card.locked" @click="lockCard(card.id)" class="text-gray-400 hover:text-blue-600 p-1.5 hover:bg-blue-50/50 rounded-lg transition" title="Geler cette carte">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            </button>
            <button v-else @click="unlockCard(card.id)" class="text-blue-500 hover:text-blue-700 p-1.5 hover:bg-blue-50/50 rounded-lg transition" title="Degeler cette carte">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/></svg>
            </button>
          </div>
        </div>

        <div v-if="!ev.cards.length" class="px-5 py-4 text-center text-gray-400 text-sm">
          Aucune carte importee
        </div>
      </div>

      <!-- Tools bar -->
      <div class="px-5 py-3 border-t border-gray-100/60 bg-white/20">
        <div class="flex items-center gap-2 flex-wrap">
          <!-- Import participants -->
          <label class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white/50 border border-white/40 rounded-xl hover:bg-white/80 cursor-pointer transition">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
            Participants
            <input type="file" accept=".xlsx,.xls" class="hidden" @change="e => importParticipants(ev.id, e)">
          </label>

          <!-- Export CSV photos par dossard -->
          <button @click="exportPhotosPerBib(ev.id)" class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white/50 border border-white/40 rounded-xl hover:bg-white/80 transition">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            CSV photos
          </button>

          <!-- Export CSV nombre photos -->
          <button @click="exportPhotoCount(ev.id)" class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white/50 border border-white/40 rounded-xl hover:bg-white/80 transition">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            CSV comptage
          </button>

          <!-- Download pack -->
          <div class="inline-flex items-center bg-white/50 border border-white/40 rounded-xl overflow-hidden">
            <input v-model="packBib[ev.id]" placeholder="Dossard" class="w-20 px-2 py-1.5 text-xs bg-transparent focus:outline-none">
            <button @click="downloadPack(ev.id)" :disabled="!packBib[ev.id]" class="px-2 py-1.5 text-xs font-medium text-blue-600 hover:bg-blue-50/50 border-l border-white/40 disabled:opacity-40 transition" title="Telecharger le pack ZIP">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            </button>
          </div>

          <!-- Cadres -->
          <button @click="openFramePanel(ev.id)" class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white/50 border border-white/40 rounded-xl hover:bg-white/80 transition">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
            Cadres
          </button>

          <!-- RGPD delete -->
          <div class="inline-flex items-center bg-red-50/50 border border-red-200/40 rounded-xl overflow-hidden">
            <input v-model="rgpdBib[ev.id]" placeholder="Dossard" class="w-20 px-2 py-1.5 text-xs bg-transparent focus:outline-none">
            <button @click="confirmRgpdDelete(ev.id)" :disabled="!rgpdBib[ev.id]" class="px-2 py-1.5 text-xs font-medium text-red-500 hover:bg-red-100/50 border-l border-red-200/40 disabled:opacity-40 transition" title="Suppression RGPD">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>

        <!-- Import result toast -->
        <div v-if="importResults[ev.id]" class="mt-2 px-3 py-2 rounded-xl text-xs" :class="importResults[ev.id].errors?.length ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'">
          {{ importResults[ev.id].imported }} importes, {{ importResults[ev.id].skipped }} ignores
          <span v-if="importResults[ev.id].errors?.length"> — {{ importResults[ev.id].errors.length }} erreur(s)</span>
          <button @click="delete importResults[ev.id]" class="ml-2 underline">Fermer</button>
        </div>

        <!-- RGPD result toast -->
        <div v-if="rgpdResults[ev.id]" class="mt-2 px-3 py-2 rounded-xl text-xs bg-red-50 text-red-700 border border-red-200">
          Dossard {{ rgpdResults[ev.id].bib_number }} : {{ rgpdResults[ev.id].web_photos_removed }} web, {{ rgpdResults[ev.id].detections_removed }} detections, {{ rgpdResults[ev.id].files_deleted }} fichiers supprimes
          <button @click="delete rgpdResults[ev.id]" class="ml-2 underline">Fermer</button>
        </div>
      </div>
    </div>

    <!-- Frame panel modal -->
    <div v-if="framePanel" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="framePanel = null">
      <div class="bg-white/90 backdrop-blur-xl border border-white/60 shadow-2xl rounded-2xl p-6 max-w-lg w-full mx-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">Cadres decoratifs</h3>
          <button @click="framePanel = null" class="text-gray-400 hover:text-gray-600 p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Upload new frame -->
        <div class="space-y-3 mb-4">
          <label class="block">
            <div class="flex items-center gap-3 px-4 py-3 bg-white/50 border border-white/40 rounded-xl cursor-pointer hover:bg-white/70 transition">
              <svg class="w-4 h-4 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              <span class="text-sm text-slate-600">{{ frameFile ? frameFile.name : 'Choisir un PNG (transparence)' }}</span>
              <input type="file" accept="image/png,image/webp" class="hidden" @change="e => frameFile = e.target.files[0]">
            </div>
          </label>
          <div class="grid grid-cols-2 gap-3">
            <input v-model="newFrame.name" placeholder="Nom du cadre" class="px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
            <div class="flex items-center gap-2">
              <label class="text-xs text-slate-500">Couleur</label>
              <input v-model="newFrame.text_color" type="color" class="w-8 h-8 rounded-lg border border-white/40 cursor-pointer">
            </div>
            <div class="flex items-center gap-2">
              <label class="text-xs text-slate-500 w-10">X</label>
              <input v-model.number="newFrame.text_x" type="range" min="0" max="1" step="0.01" class="flex-1">
              <span class="text-xs text-slate-400 w-8 text-right">{{ Math.round(newFrame.text_x * 100) }}%</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-xs text-slate-500 w-10">Y</label>
              <input v-model.number="newFrame.text_y" type="range" min="0" max="1" step="0.01" class="flex-1">
              <span class="text-xs text-slate-400 w-8 text-right">{{ Math.round(newFrame.text_y * 100) }}%</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-xs text-slate-500 w-10">Taille</label>
              <input v-model.number="newFrame.text_size" type="range" min="12" max="120" step="1" class="flex-1">
              <span class="text-xs text-slate-400 w-8 text-right">{{ newFrame.text_size }}px</span>
            </div>
            <button @click="uploadFrame" :disabled="!frameFile" class="px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600 disabled:opacity-40 transition">
              Ajouter
            </button>
          </div>
        </div>

        <!-- Existing frames -->
        <div v-if="frames[framePanel]?.length" class="space-y-2 mb-4">
          <div v-for="f in frames[framePanel]" :key="f.id" class="flex items-center justify-between px-3 py-2 bg-white/50 border border-white/40 rounded-xl">
            <div>
              <span class="text-sm font-medium text-slate-700">{{ f.name }}</span>
              <span class="text-xs text-slate-400 ml-2">{{ f.text_size }}px, {{ Math.round(f.text_x*100) }}%x{{ Math.round(f.text_y*100) }}%</span>
            </div>
            <button @click="deleteFrame(framePanel, f.id)" class="text-red-400 hover:text-red-600 p-1 transition">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400 mb-4">Aucun cadre configure</p>

        <!-- Generate framed pack -->
        <div class="border-t border-gray-100 pt-3">
          <p class="text-xs font-medium text-slate-600 mb-2">Generer un pack avec cadre</p>
          <div class="flex gap-2">
            <input v-model="framedBib" placeholder="Dossard" class="flex-1 px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
            <select v-model="selectedFrameId" class="px-3 py-2 bg-white/50 border border-white/40 rounded-xl text-sm focus:outline-none">
              <option value="">Cadre...</option>
              <option v-for="f in frames[framePanel]" :key="f.id" :value="f.id">{{ f.name }}</option>
            </select>
            <button @click="downloadFramedPack" :disabled="!framedBib || !selectedFrameId" class="px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600 disabled:opacity-40 transition">
              ZIP
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- RGPD Confirmation Modal -->
    <div v-if="showRgpdModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div class="bg-white/90 backdrop-blur-xl border border-white/60 shadow-2xl rounded-2xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold text-slate-800 mb-2">Confirmer la suppression RGPD</h3>
        <p class="text-sm text-slate-600 mb-4">
          Cette action est <strong>irreversible</strong>. Toutes les photos du dossard <strong>{{ rgpdBib[showRgpdModal] }}</strong> seront supprimees du site web et du serveur.
        </p>
        <div class="flex justify-end gap-3">
          <button @click="showRgpdModal = null" class="px-4 py-2 text-sm text-slate-600 bg-white/70 border border-white/60 rounded-xl hover:bg-white/90 transition">Annuler</button>
          <button @click="executeRgpdDelete" class="px-4 py-2 text-sm text-white bg-red-500 rounded-xl hover:bg-red-600 transition">Supprimer</button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && !events.length" class="text-center py-16">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      <h3 class="text-lg font-medium text-gray-600 mb-1">Aucune course</h3>
      <p class="text-gray-400">Creez une course dans l'onglet Courses pour commencer</p>
    </div>

    <!-- Auto-refresh toggle -->
    <div class="fixed bottom-6 right-6">
      <button @click="toggleAutoRefresh" class="bg-white/70 backdrop-blur-xl shadow-lg border border-white/60 rounded-2xl px-4 py-2 text-sm flex items-center gap-2 transition hover:bg-white/90"
        :class="autoRefresh ? 'text-green-600' : 'text-gray-500'">
        <div class="w-2 h-2 rounded-full" :class="autoRefresh ? 'bg-green-500 animate-pulse' : 'bg-gray-300'"></div>
        {{ autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import { triOverviewApi, triToolsApi } from '../../api/events'
import { useToast } from '../../composables/useToast'
const toast = useToast()

const loading = ref(false)
const events = ref([])
const global = ref({ total_events: 0, active_events: 0, total_photos: 0, total_processed: 0, total_validated: 0, total_bibs: 0 })
const autoRefresh = ref(true)
let refreshInterval = null

// Tools state
const packBib = reactive({})
const rgpdBib = reactive({})
const importResults = reactive({})
const rgpdResults = reactive({})
const framePanel = ref(null)
const frames = reactive({})
const frameFile = ref(null)
const newFrame = ref({ name: 'Cadre', text_x: 0.5, text_y: 0.9, text_size: 48, text_color: '#FFFFFF' })
const framedBib = ref('')
const selectedFrameId = ref('')
const showRgpdModal = ref(null)

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

function getCardState(card) {
  if (card.locked) return 'locked'
  if (card.status === 'importing') return 'importing'
  if (card.status === 'error') return 'error'
  if (card.processed === card.photo_count && card.photo_count > 0) return 'done'
  return 'pending'
}

function cardStatusBg(card) {
  const state = getCardState(card)
  const map = {
    locked: 'bg-gray-200/80',
    importing: 'bg-blue-100/80',
    done: 'bg-green-100/80',
    error: 'bg-red-100/80',
    pending: 'bg-gray-100/80',
  }
  return map[state] || 'bg-gray-100/80'
}

async function loadData() {
  loading.value = true
  try {
    const res = await triOverviewApi.overview()
    global.value = res.data.global_stats
    events.value = res.data.events
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function lockCard(cardId) {
  try {
    await triOverviewApi.lockCard(cardId)
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function unlockCard(cardId) {
  try {
    await triOverviewApi.unlockCard(cardId)
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function processEvent(eventId) {
  try {
    await triOverviewApi.processAll(eventId)
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function stopEvent(eventId) {
  try {
    await triOverviewApi.stopEvent(eventId)
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

// --- Tool actions ---

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function importParticipants(eventId, e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const { data } = await triToolsApi.importParticipants(eventId, file)
    importResults[eventId] = data
  } catch (err) {
    importResults[eventId] = { imported: 0, skipped: 0, errors: [err.response?.data?.detail || 'Erreur'] }
  }
  e.target.value = ''
}

async function exportPhotosPerBib(eventId) {
  try {
    const { data } = await triToolsApi.exportPhotosPerBib(eventId)
    triggerDownload(data, `photos_par_dossard_${eventId}.csv`)
  } catch { /* ignore */ }
}

async function exportPhotoCount(eventId) {
  try {
    const { data } = await triToolsApi.exportPhotoCount(eventId)
    triggerDownload(data, `nombre_photos_${eventId}.csv`)
  } catch { /* ignore */ }
}

async function downloadPack(eventId) {
  const bib = packBib[eventId]
  if (!bib) return
  try {
    const { data } = await triToolsApi.downloadPack(eventId, bib)
    triggerDownload(data, `pack_${bib}.zip`)
  } catch { /* ignore */ }
}

async function openFramePanel(eventId) {
  framePanel.value = eventId
  try {
    const { data } = await triToolsApi.listFrames(eventId)
    frames[eventId] = data
  } catch { frames[eventId] = [] }
}

async function uploadFrame() {
  if (!frameFile.value || !framePanel.value) return
  try {
    await triToolsApi.createFrame(framePanel.value, frameFile.value, newFrame.value)
    frameFile.value = null
    newFrame.value = { name: 'Cadre', text_x: 0.5, text_y: 0.9, text_size: 48, text_color: '#FFFFFF' }
    const { data } = await triToolsApi.listFrames(framePanel.value)
    frames[framePanel.value] = data
  } catch { /* ignore */ }
}

async function deleteFrame(eventId, frameId) {
  try {
    await triToolsApi.deleteFrame(eventId, frameId)
    const { data } = await triToolsApi.listFrames(eventId)
    frames[eventId] = data
  } catch { /* ignore */ }
}

async function downloadFramedPack() {
  if (!framedBib.value || !selectedFrameId.value || !framePanel.value) return
  try {
    const { data } = await triToolsApi.generateFramedPack(framePanel.value, selectedFrameId.value, framedBib.value)
    triggerDownload(data, `pack_cadre_${framedBib.value}.zip`)
  } catch { /* ignore */ }
}

function confirmRgpdDelete(eventId) {
  if (!rgpdBib[eventId]) return
  showRgpdModal.value = eventId
}

async function executeRgpdDelete() {
  const eventId = showRgpdModal.value
  const bib = rgpdBib[eventId]
  showRgpdModal.value = null
  try {
    const { data } = await triToolsApi.rgpdDelete(eventId, bib)
    rgpdResults[eventId] = data
    await loadData()
  } catch (e) {
    rgpdResults[eventId] = { bib_number: bib, web_photos_removed: 0, detections_removed: 0, files_deleted: 0 }
  }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  refreshInterval = setInterval(loadData, 5000)
}

function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

onMounted(() => {
  loadData()
  if (autoRefresh.value) startAutoRefresh()
})

onUnmounted(stopAutoRefresh)
</script>
