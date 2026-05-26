<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="px-6 py-4 bg-white/70 backdrop-blur-xl border-b border-white/60 shrink-0">
      <h1 class="text-xl font-bold text-gray-900">Centre d'Entrainement IA</h1>
      <p class="text-sm text-gray-500 mt-0.5">Ameliorez progressivement les performances du systeme</p>
    </div>

    <!-- Tabs -->
    <div class="px-6 pt-3 bg-white/50 border-b border-gray-200/60 shrink-0">
      <div class="flex gap-1">
        <button v-for="t in tabs" :key="t.id" @click="activeTab = t.id"
          :class="['px-4 py-2.5 text-sm font-medium rounded-t-xl transition-all border-b-2',
            activeTab === t.id ? 'bg-white text-blue-600 border-blue-500 shadow-sm' : 'text-gray-500 hover:text-gray-700 border-transparent hover:bg-white/50']">
          {{ t.label }}
          <span v-if="t.badge" class="ml-1.5 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">{{ t.badge }}</span>
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6">

      <!-- ═══ DASHBOARD ═══ -->
      <div v-if="activeTab === 'dashboard'">
        <div v-if="!dashboard" class="text-center py-12 text-gray-400">Chargement...</div>
        <template v-else>
          <!-- KPIs -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white/70 backdrop-blur-xl rounded-2xl p-4 border border-white/60 shadow-sm">
              <p class="text-xs text-gray-500 uppercase tracking-wider">Corrections</p>
              <p class="text-2xl font-bold text-gray-900 mt-1">{{ dashboard.total_corrections }}</p>
            </div>
            <div class="bg-white/70 backdrop-blur-xl rounded-2xl p-4 border border-white/60 shadow-sm">
              <p class="text-xs text-gray-500 uppercase tracking-wider">Precision IA</p>
              <p class="text-2xl font-bold mt-1" :class="dashboard.accuracy_rate > 0.8 ? 'text-green-600' : dashboard.accuracy_rate > 0.5 ? 'text-amber-600' : 'text-red-600'">
                {{ (dashboard.accuracy_rate * 100).toFixed(1) }}%
              </p>
            </div>
            <div class="bg-white/70 backdrop-blur-xl rounded-2xl p-4 border border-white/60 shadow-sm">
              <p class="text-xs text-gray-500 uppercase tracking-wider">En attente</p>
              <p class="text-2xl font-bold text-amber-600 mt-1">{{ dashboard.pending_reviews }}</p>
            </div>
            <div class="bg-white/70 backdrop-blur-xl rounded-2xl p-4 border border-white/60 shadow-sm">
              <p class="text-xs text-gray-500 uppercase tracking-wider">Datasets</p>
              <p class="text-2xl font-bold text-gray-900 mt-1">{{ dashboard.total_entries }} entrees</p>
            </div>
          </div>

          <!-- Errors breakdown -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="bg-white/70 backdrop-blur-xl rounded-2xl p-5 border border-white/60 shadow-sm">
              <h3 class="text-sm font-bold text-gray-700 mb-3">Erreurs par type</h3>
              <div v-if="Object.keys(dashboard.errors_by_type).length" class="space-y-2">
                <div v-for="(count, type) in dashboard.errors_by_type" :key="type" class="flex items-center gap-3">
                  <span class="text-xs px-2 py-1 rounded-lg font-medium" :class="errorBadge(type)">{{ errorLabel(type) }}</span>
                  <div class="flex-1 bg-gray-100 rounded-full h-2">
                    <div class="h-2 rounded-full bg-red-400" :style="{ width: Math.min(100, count / maxError * 100) + '%' }"></div>
                  </div>
                  <span class="text-sm font-bold text-gray-600">{{ count }}</span>
                </div>
              </div>
              <p v-else class="text-sm text-gray-400">Aucune erreur enregistree</p>
            </div>

            <div class="bg-white/70 backdrop-blur-xl rounded-2xl p-5 border border-white/60 shadow-sm">
              <h3 class="text-sm font-bold text-gray-700 mb-3">Files de validation</h3>
              <div v-if="Object.keys(dashboard.reviews_by_queue).length" class="space-y-2">
                <div v-for="(count, queue) in dashboard.reviews_by_queue" :key="queue" class="flex items-center justify-between py-1">
                  <span class="text-sm text-gray-600">{{ queueLabel(queue) }}</span>
                  <span class="text-sm font-bold px-2 py-0.5 rounded-lg bg-amber-100 text-amber-700">{{ count }}</span>
                </div>
              </div>
              <p v-else class="text-sm text-gray-400">Aucun element en attente</p>
            </div>
          </div>

          <!-- Suggestions -->
          <div v-if="dashboard.suggestions?.length" class="mb-6">
            <h3 class="text-sm font-bold text-gray-700 mb-3">Suggestions d'amelioration</h3>
            <div class="space-y-2">
              <div v-for="s in dashboard.suggestions" :key="s.title"
                class="bg-white/70 backdrop-blur-xl rounded-xl p-4 border-l-4 shadow-sm flex items-center gap-4"
                :class="s.priority === 'high' ? 'border-red-400' : 'border-amber-400'">
                <div class="flex-1">
                  <p class="text-sm font-bold text-gray-800">{{ s.title }}</p>
                  <p class="text-xs text-gray-500 mt-0.5">{{ s.description }}</p>
                </div>
                <span :class="s.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'" class="text-xs font-bold px-2 py-1 rounded-lg uppercase">{{ s.priority }}</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-3">
            <button @click="collectAllGT" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg shadow-blue-500/25 transition">
              Collecter les corrections
            </button>
            <button @click="flagAllEvents" class="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg shadow-amber-500/25 transition">
              Analyser cas problematiques
            </button>
          </div>
        </template>
      </div>

      <!-- ═══ REVIEW QUEUE ═══ -->
      <div v-if="activeTab === 'review'">
        <!-- Queue filters -->
        <div class="flex items-center gap-2 mb-4">
          <select v-model="reviewQueue" @change="loadReview" class="px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm">
            <option value="">Toutes les files</option>
            <option value="to_review">A verifier</option>
            <option value="difficult">Cas difficiles</option>
            <option value="hallucination">Hallucinations</option>
            <option value="ocr_ambiguous">OCR ambigu</option>
            <option value="multi_bib">Multi-dossards</option>
            <option value="bad_detection">Mauvaises detections</option>
            <option value="rotation">Rotation</option>
            <option value="blur">Flou</option>
          </select>
          <span class="text-sm text-gray-500">{{ reviewItems.length }} elements</span>
        </div>

        <!-- Review items -->
        <div v-if="!reviewItems.length" class="text-center py-12 text-gray-400">
          <p>Aucun element en attente</p>
          <p class="text-xs mt-1">Lancez l'analyse depuis le dashboard pour detecter les cas problematiques</p>
        </div>
        <div v-else class="space-y-2">
          <div v-for="item in reviewItems" :key="item.id"
            class="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/60 shadow-sm p-4 flex items-center gap-4 hover:border-blue-300/60 transition cursor-pointer"
            @click="openReviewItem(item)">
            <div class="w-16 h-16 rounded-xl overflow-hidden bg-gray-100 shrink-0">
              <img v-if="item.photo_filepath" :src="reviewPhotoUrl(item)" class="w-full h-full object-cover" loading="lazy">
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-bold px-2 py-0.5 rounded-lg" :class="reasonBadge(item.reason)">{{ reasonLabel(item.reason) }}</span>
                <span v-if="item.bib_number" class="text-xs font-bold text-green-700">#{{ item.bib_number }}</span>
                <span class="text-xs text-gray-400">{{ item.photo_filename }}</span>
              </div>
              <p v-if="item.ocr_raw_response" class="text-xs text-gray-500 truncate">OCR: {{ item.ocr_raw_response }}</p>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span class="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">P{{ item.priority }}</span>
              <button @click.stop="quickResolve(item, 'confirmed')" class="bg-green-100 hover:bg-green-200 text-green-700 px-3 py-1.5 rounded-lg text-xs font-medium transition">OK</button>
              <button @click.stop="quickResolve(item, 'rejected')" class="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1.5 rounded-lg text-xs font-medium transition">Rejeter</button>
            </div>
          </div>
        </div>

        <!-- Review modal -->
        <div v-if="reviewModalOpen" class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" @click.self="reviewModalOpen = false">
          <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div class="p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-gray-900">Verification</h3>
                <button @click="reviewModalOpen = false" class="text-gray-400 hover:text-gray-600">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>

              <div class="grid grid-cols-2 gap-4 mb-4" v-if="activeReviewItem">
                <!-- Photo -->
                <div class="relative">
                  <img v-if="activeReviewItem.photo_filepath" :src="reviewPhotoUrl(activeReviewItem)" class="w-full rounded-xl">
                </div>
                <!-- Info -->
                <div class="space-y-3">
                  <div class="bg-gray-50 rounded-xl p-3">
                    <p class="text-xs text-gray-500 mb-1">Resultat IA</p>
                    <p class="text-lg font-bold">{{ activeReviewItem.bib_number || 'Aucun' }}</p>
                    <p class="text-xs text-gray-500 mt-1">Confiance OCR: {{ (activeReviewItem.confidence_ocr * 100).toFixed(0) }}%</p>
                    <p class="text-xs text-gray-500">Classification: {{ activeReviewItem.classification }}</p>
                    <p v-if="activeReviewItem.fallback_used" class="text-xs text-amber-600 mt-1">Fallback utilise</p>
                  </div>
                  <div class="bg-gray-50 rounded-xl p-3">
                    <p class="text-xs text-gray-500 mb-1">Reponse brute</p>
                    <code class="text-xs text-gray-700 break-all">{{ activeReviewItem.ocr_raw_response || 'N/A' }}</code>
                  </div>
                  <div class="bg-gray-50 rounded-xl p-3">
                    <p class="text-xs text-gray-500 mb-1">Raison du signalement</p>
                    <span class="text-xs font-bold px-2 py-1 rounded-lg" :class="reasonBadge(activeReviewItem.reason)">{{ reasonLabel(activeReviewItem.reason) }}</span>
                  </div>

                  <!-- Correction form -->
                  <div class="border-t pt-3">
                    <label class="text-xs text-gray-500 block mb-1">Numero corrige</label>
                    <input v-model="correctionBib" type="text" class="w-full px-3 py-2 border rounded-xl text-sm" placeholder="Numero correct ou vide">
                    <label class="text-xs text-gray-500 block mt-2 mb-1">Classification</label>
                    <select v-model="correctionClass" class="w-full px-3 py-2 border rounded-xl text-sm">
                      <option value="bon">Bon</option>
                      <option value="mauvais">Mauvais</option>
                      <option value="flou">Flou</option>
                      <option value="coupe">Coupe</option>
                      <option value="incertain">Incertain</option>
                    </select>
                    <label class="text-xs text-gray-500 block mt-2 mb-1">Type d'erreur</label>
                    <select v-model="correctionErrorType" class="w-full px-3 py-2 border rounded-xl text-sm">
                      <option value="">Non specifie</option>
                      <option value="hallucination">Hallucination</option>
                      <option value="digit_confusion">Confusion chiffres</option>
                      <option value="digit_count">Mauvais nb chiffres</option>
                      <option value="missed_bib">Dossard manque</option>
                      <option value="false_positive">Faux positif</option>
                      <option value="rotation">Mauvaise rotation</option>
                      <option value="blur_false_positive">Faux flou</option>
                    </select>
                    <label class="text-xs text-gray-500 block mt-2 mb-1">Difficulte</label>
                    <select v-model="correctionDifficulty" class="w-full px-3 py-2 border rounded-xl text-sm">
                      <option value="easy">Facile</option>
                      <option value="normal">Normal</option>
                      <option value="hard">Difficile</option>
                      <option value="extreme">Extreme</option>
                    </select>
                  </div>

                  <div class="flex gap-2 pt-2">
                    <button @click="resolveReview('corrected')" class="flex-1 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition">Corriger</button>
                    <button @click="resolveReview('confirmed')" class="flex-1 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition">Confirmer</button>
                    <button @click="resolveReview('rejected')" class="flex-1 bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition">Rejeter</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ GROUND TRUTH ═══ -->
      <div v-if="activeTab === 'groundtruth'">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <select v-model="gtFilter.error_type" @change="loadGroundTruth" class="px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm">
              <option value="">Tous types</option>
              <option value="hallucination">Hallucination</option>
              <option value="digit_confusion">Confusion chiffres</option>
              <option value="digit_count">Nb chiffres</option>
              <option value="missed_bib">Dossard manque</option>
              <option value="false_positive">Faux positif</option>
            </select>
            <select v-model="gtFilter.is_correct" @change="loadGroundTruth" class="px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm">
              <option value="">Tous</option>
              <option value="true">Correct</option>
              <option value="false">Erreur</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">{{ groundTruths.length }} entrees</span>
            <button @click="collectAllGT" class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-xl text-xs font-medium transition">Collecter</button>
          </div>
        </div>

        <div v-if="!groundTruths.length" class="text-center py-12 text-gray-400">Aucune donnee. Collectez depuis les corrections validees.</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs text-gray-500 uppercase border-b">
                <th class="pb-2 px-2">Photo</th>
                <th class="pb-2 px-2">IA</th>
                <th class="pb-2 px-2">Humain</th>
                <th class="pb-2 px-2">Correct</th>
                <th class="pb-2 px-2">Type erreur</th>
                <th class="pb-2 px-2">Sport</th>
                <th class="pb-2 px-2">Difficulte</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="gt in groundTruths" :key="gt.id" class="border-b border-gray-100 hover:bg-white/50">
                <td class="py-2 px-2 text-gray-600">{{ gt.photo_id }}</td>
                <td class="py-2 px-2">
                  <span class="font-mono">{{ gt.ai_bib || '-' }}</span>
                  <span class="text-xs text-gray-400 ml-1">{{ gt.ai_classification }}</span>
                </td>
                <td class="py-2 px-2 font-bold">{{ gt.human_bib || '-' }}</td>
                <td class="py-2 px-2">
                  <span :class="gt.is_correct ? 'text-green-600' : 'text-red-600'" class="font-bold">{{ gt.is_correct ? 'OK' : 'ERR' }}</span>
                </td>
                <td class="py-2 px-2">
                  <span v-if="gt.error_type" class="text-xs px-2 py-0.5 rounded-lg" :class="errorBadge(gt.error_type)">{{ errorLabel(gt.error_type) }}</span>
                </td>
                <td class="py-2 px-2 text-gray-500">{{ gt.sport_type || '-' }}</td>
                <td class="py-2 px-2">
                  <span class="text-xs px-2 py-0.5 rounded-lg" :class="diffBadge(gt.difficulty)">{{ gt.difficulty }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ═══ DATASETS ═══ -->
      <div v-if="activeTab === 'datasets'">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-gray-700">Datasets d'entrainement</h3>
          <button @click="showCreateDataset = true" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition">Nouveau dataset</button>
        </div>

        <div v-if="!datasets.length" class="text-center py-12 text-gray-400">Aucun dataset. Creez-en un pour commencer.</div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="ds in datasets" :key="ds.id" class="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/60 shadow-sm p-5">
            <div class="flex items-center justify-between mb-3">
              <h4 class="font-bold text-gray-800">{{ ds.name }}</h4>
              <span class="text-xs px-2 py-1 rounded-lg" :class="ds.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'">{{ ds.status }}</span>
            </div>
            <p v-if="ds.description" class="text-xs text-gray-500 mb-3">{{ ds.description }}</p>
            <div class="flex items-center gap-4 text-xs text-gray-500 mb-3">
              <span>{{ ds.entry_count }} entrees</span>
              <span class="text-green-600">{{ ds.correct_count }} correct</span>
              <span class="text-red-600">{{ ds.error_count }} erreurs</span>
            </div>
            <div v-if="ds.tags" class="flex flex-wrap gap-1 mb-3">
              <span v-for="tag in ds.tags.split(',')" :key="tag" class="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{{ tag.trim() }}</span>
            </div>
            <div class="flex gap-2">
              <button @click="addAllToDataset(ds.id)" class="flex-1 bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1.5 rounded-lg text-xs font-medium transition">+ Ajouter tout</button>
              <button @click="deleteDataset(ds.id)" class="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1.5 rounded-lg text-xs font-medium transition">Suppr</button>
            </div>
          </div>
        </div>

        <!-- Create dataset modal -->
        <div v-if="showCreateDataset" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" @click.self="showCreateDataset = false">
          <div class="bg-white rounded-2xl p-6 w-96 shadow-2xl">
            <h3 class="text-lg font-bold mb-4">Nouveau dataset</h3>
            <input v-model="newDataset.name" type="text" placeholder="Nom" class="w-full px-3 py-2 border rounded-xl text-sm mb-3">
            <textarea v-model="newDataset.description" placeholder="Description" class="w-full px-3 py-2 border rounded-xl text-sm mb-3" rows="2"></textarea>
            <input v-model="newDataset.tags" type="text" placeholder="Tags (comma-sep)" class="w-full px-3 py-2 border rounded-xl text-sm mb-4">
            <div class="flex gap-2">
              <button @click="createDataset" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium">Creer</button>
              <button @click="showCreateDataset = false" class="bg-gray-200 px-4 py-2 rounded-xl text-sm">Annuler</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ MODELS ═══ -->
      <div v-if="activeTab === 'models'">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-gray-700">Versions des modeles</h3>
          <button @click="showCreateModel = true" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition">Enregistrer modele</button>
        </div>

        <div v-if="!models.length" class="text-center py-12 text-gray-400">Aucun modele enregistre</div>
        <div v-else class="space-y-3">
          <div v-for="m in models" :key="m.id"
            class="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/60 shadow-sm p-5">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-3">
                <h4 class="font-bold text-gray-800">{{ m.name }}</h4>
                <span class="text-xs text-gray-400">v{{ m.version }}</span>
                <span class="text-xs px-2 py-0.5 rounded-lg font-medium" :class="modelStatusBadge(m.status)">{{ m.status }}</span>
              </div>
              <span class="text-xs px-2 py-1 rounded-lg bg-gray-100 text-gray-600">{{ m.model_type }}</span>
            </div>
            <p v-if="m.description" class="text-xs text-gray-500 mb-3">{{ m.description }}</p>

            <!-- Metrics -->
            <div v-if="m.accuracy != null" class="grid grid-cols-4 gap-3 mb-3">
              <div class="text-center">
                <p class="text-xs text-gray-500">Precision</p>
                <p class="font-bold text-sm">{{ m.accuracy != null ? (m.accuracy * 100).toFixed(1) + '%' : '-' }}</p>
              </div>
              <div class="text-center">
                <p class="text-xs text-gray-500">F1</p>
                <p class="font-bold text-sm">{{ m.f1_score != null ? (m.f1_score * 100).toFixed(1) + '%' : '-' }}</p>
              </div>
              <div class="text-center">
                <p class="text-xs text-gray-500">Hallucinations</p>
                <p class="font-bold text-sm">{{ m.hallucination_rate != null ? (m.hallucination_rate * 100).toFixed(1) + '%' : '-' }}</p>
              </div>
              <div class="text-center">
                <p class="text-xs text-gray-500">Vitesse</p>
                <p class="font-bold text-sm">{{ m.avg_inference_time != null ? m.avg_inference_time.toFixed(0) + 'ms' : '-' }}</p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-2">
              <button v-if="m.status === 'candidate'" @click="promoteModel(m.id, 'validated')" class="bg-green-100 hover:bg-green-200 text-green-700 px-3 py-1.5 rounded-lg text-xs font-medium transition">Valider</button>
              <button v-if="m.status === 'validated'" @click="promoteModel(m.id, 'production')" class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition shadow">Deployer en production</button>
              <button v-if="m.status !== 'archived'" @click="promoteModel(m.id, 'archived')" class="bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg text-xs font-medium transition">Archiver</button>
            </div>
          </div>
        </div>

        <!-- Create model modal -->
        <div v-if="showCreateModel" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" @click.self="showCreateModel = false">
          <div class="bg-white rounded-2xl p-6 w-96 shadow-2xl">
            <h3 class="text-lg font-bold mb-4">Enregistrer un modele</h3>
            <input v-model="newModel.name" type="text" placeholder="Nom (ex: YOLO_v2_trail)" class="w-full px-3 py-2 border rounded-xl text-sm mb-3">
            <select v-model="newModel.model_type" class="w-full px-3 py-2 border rounded-xl text-sm mb-3">
              <option value="yolo">YOLO (detection)</option>
              <option value="ocr">OCR (dossards)</option>
              <option value="scorer">Scorer</option>
              <option value="rotation">Rotation</option>
            </select>
            <input v-model="newModel.version" type="text" placeholder="Version (ex: 2.0)" class="w-full px-3 py-2 border rounded-xl text-sm mb-3">
            <textarea v-model="newModel.description" placeholder="Description" class="w-full px-3 py-2 border rounded-xl text-sm mb-3" rows="2"></textarea>
            <input v-model="newModel.model_path" type="text" placeholder="Chemin modele (optionnel)" class="w-full px-3 py-2 border rounded-xl text-sm mb-4">
            <div class="flex gap-2">
              <button @click="createModel" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium">Enregistrer</button>
              <button @click="showCreateModel = false" class="bg-gray-200 px-4 py-2 rounded-xl text-sm">Annuler</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ TRAINING SESSIONS ═══ -->
      <div v-if="activeTab === 'sessions'">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-bold text-gray-700">Sessions d'entrainement</h3>
        </div>
        <div v-if="!sessions.length" class="text-center py-12 text-gray-400">
          <p>Aucune session d'entrainement</p>
          <p class="text-xs mt-1">Les sessions seront disponibles quand vous aurez suffisamment de donnees</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="s in sessions" :key="s.id" class="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/60 shadow-sm p-5">
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-bold text-gray-800">{{ s.name }}</h4>
              <span class="text-xs px-2 py-1 rounded-lg" :class="sessionStatusBadge(s.status)">{{ s.status }}</span>
            </div>
            <div v-if="s.status === 'running'" class="mb-2">
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-blue-500 h-2 rounded-full transition-all" :style="{ width: s.progress + '%' }"></div>
              </div>
              <p class="text-xs text-gray-500 mt-1">{{ s.progress.toFixed(0) }}%</p>
            </div>
            <div class="text-xs text-gray-500">
              <span>Type: {{ s.model_type }}</span>
              <span v-if="s.epochs" class="ml-3">Epochs: {{ s.epochs }}</span>
              <span v-if="s.best_metric != null" class="ml-3">Best: {{ (s.best_metric * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { trainingApi } from '../../api/training'
import { useToast } from '../../composables/useToast'

const toast = useToast()

// ─── State ───
const activeTab = ref('dashboard')
const dashboard = ref(null)
const reviewItems = ref([])
const reviewQueue = ref('')
const groundTruths = ref([])
const datasets = ref([])
const models = ref([])
const sessions = ref([])

// Modals
const reviewModalOpen = ref(false)
const activeReviewItem = ref(null)
const showCreateDataset = ref(false)
const showCreateModel = ref(false)

// Forms
const correctionBib = ref('')
const correctionClass = ref('bon')
const correctionErrorType = ref('')
const correctionDifficulty = ref('normal')
const newDataset = reactive({ name: '', description: '', tags: '' })
const newModel = reactive({ name: '', model_type: 'ocr', version: '1.0', description: '', model_path: '' })
const gtFilter = reactive({ error_type: '', is_correct: '' })

// ─── Tabs ───
const tabs = computed(() => [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'review', label: 'File de validation', badge: dashboard.value?.pending_reviews || 0 },
  { id: 'groundtruth', label: 'Ground Truth' },
  { id: 'datasets', label: 'Datasets' },
  { id: 'models', label: 'Modeles' },
  { id: 'sessions', label: 'Entrainements' },
])

const maxError = computed(() => {
  if (!dashboard.value?.errors_by_type) return 1
  return Math.max(1, ...Object.values(dashboard.value.errors_by_type))
})

// ─── Loaders ───
async function loadDashboard() {
  try {
    const res = await trainingApi.dashboard()
    dashboard.value = res.data
  } catch { dashboard.value = { total_corrections: 0, correct_predictions: 0, accuracy_rate: 0, errors_by_type: {}, errors_by_sport: {}, errors_by_weather: {}, errors_by_lighting: {}, pending_reviews: 0, reviews_by_queue: {}, total_datasets: 0, total_entries: 0, models_by_status: {}, production_models: [], suggestions: [] } }
}

async function loadReview() {
  try {
    const params = { status: 'pending' }
    if (reviewQueue.value) params.queue = reviewQueue.value
    const res = await trainingApi.listReview(params)
    reviewItems.value = res.data
  } catch { reviewItems.value = [] }
}

async function loadGroundTruth() {
  try {
    const params = {}
    if (gtFilter.error_type) params.error_type = gtFilter.error_type
    if (gtFilter.is_correct !== '') params.is_correct = gtFilter.is_correct === 'true'
    const res = await trainingApi.listGroundTruth(params)
    groundTruths.value = res.data
  } catch { groundTruths.value = [] }
}

async function loadDatasets() {
  try { datasets.value = (await trainingApi.listDatasets()).data } catch { datasets.value = [] }
}

async function loadModels() {
  try { models.value = (await trainingApi.listModels()).data } catch { models.value = [] }
}

async function loadSessions() {
  try { sessions.value = (await trainingApi.listSessions()).data } catch { sessions.value = [] }
}

// ─── Actions ───
async function collectAllGT() {
  try {
    const res = await trainingApi.collectAll()
    toast.success(`${res.data.count} corrections collectees`)
    loadDashboard()
    loadGroundTruth()
  } catch (e) { toast.error('Erreur: ' + (e.response?.data?.detail || e.message)) }
}

async function flagAllEvents() {
  try {
    // Get all events and flag each
    const evRes = await import('../../api/events').then(m => m.eventsApi.list())
    let total = 0
    for (const ev of evRes.data) {
      const res = await trainingApi.flagEvent(ev.id)
      total += res.data.count
    }
    toast.success(`${total} cas problematiques detectes`)
    loadDashboard()
    loadReview()
  } catch (e) { toast.error('Erreur: ' + (e.response?.data?.detail || e.message)) }
}

function openReviewItem(item) {
  activeReviewItem.value = item
  correctionBib.value = item.bib_number || ''
  correctionClass.value = item.classification || 'bon'
  correctionErrorType.value = ''
  correctionDifficulty.value = 'normal'
  reviewModalOpen.value = true
}

async function resolveReview(resolution) {
  if (!activeReviewItem.value) return
  try {
    const data = { resolution }
    if (resolution === 'corrected') {
      data.corrected_bib = correctionBib.value || null
      data.corrected_class = correctionClass.value
      data.error_type = correctionErrorType.value || null
      data.difficulty = correctionDifficulty.value
    }
    await trainingApi.resolveReview(activeReviewItem.value.id, data)
    reviewItems.value = reviewItems.value.filter(i => i.id !== activeReviewItem.value.id)
    reviewModalOpen.value = false
    toast.success('Resolution enregistree')
    loadDashboard()
  } catch (e) { toast.error('Erreur') }
}

async function quickResolve(item, resolution) {
  try {
    await trainingApi.resolveReview(item.id, { resolution })
    reviewItems.value = reviewItems.value.filter(i => i.id !== item.id)
    if (dashboard.value) dashboard.value.pending_reviews--
  } catch {}
}

async function createDataset() {
  try {
    await trainingApi.createDataset({ name: newDataset.name, description: newDataset.description, tags: newDataset.tags })
    showCreateDataset.value = false
    newDataset.name = ''; newDataset.description = ''; newDataset.tags = ''
    loadDatasets()
    toast.success('Dataset cree')
  } catch (e) { toast.error('Erreur') }
}

async function addAllToDataset(dsId) {
  try {
    const res = await trainingApi.addEntries(dsId, {})
    toast.success(`${res.data.count} entrees ajoutees`)
    loadDatasets()
  } catch (e) { toast.error('Erreur') }
}

async function deleteDataset(dsId) {
  try {
    await trainingApi.deleteDataset(dsId)
    loadDatasets()
  } catch {}
}

async function createModel() {
  try {
    await trainingApi.createModel(newModel)
    showCreateModel.value = false
    Object.assign(newModel, { name: '', model_type: 'ocr', version: '1.0', description: '', model_path: '' })
    loadModels()
    toast.success('Modele enregistre')
  } catch (e) { toast.error('Erreur') }
}

async function promoteModel(id, status) {
  try {
    await trainingApi.promoteModel(id, status)
    loadModels()
    toast.success(`Modele promu: ${status}`)
  } catch (e) { toast.error('Erreur') }
}

// ─── Helpers ───
function reviewPhotoUrl(item) {
  const parts = item.photo_filepath?.split('/') || []
  const eventDir = parts[parts.length - 2] || ''
  const filename = parts[parts.length - 1] || ''
  return `/uploads/${eventDir}/${filename}`
}

const errorLabels = { hallucination: 'Hallucination', digit_confusion: 'Confusion chiffres', digit_count: 'Nb chiffres', missed_bib: 'Dossard manque', false_positive: 'Faux positif', rotation: 'Rotation', blur_false_positive: 'Faux flou' }
function errorLabel(t) { return errorLabels[t] || t }
function errorBadge(t) {
  const m = { hallucination: 'bg-red-100 text-red-700', digit_confusion: 'bg-amber-100 text-amber-700', missed_bib: 'bg-blue-100 text-blue-700', false_positive: 'bg-purple-100 text-purple-700' }
  return m[t] || 'bg-gray-100 text-gray-600'
}

const queueLabels = { to_review: 'A verifier', difficult: 'Cas difficiles', hallucination: 'Hallucinations', ocr_ambiguous: 'OCR ambigu', multi_bib: 'Multi-dossards', bad_detection: 'Mauvaises detections', rotation: 'Rotation', blur: 'Flou', user_error: 'Erreurs utilisateur' }
function queueLabel(q) { return queueLabels[q] || q }

const reasonLabels = { low_confidence: 'Faible confiance', ocr_ambiguous: 'OCR ambigu', multi_bib: 'Multi-dossards', fallback: 'Fallback', hallucination: 'Hallucination', bad_bbox: 'Mauvaise bbox', rotation_doubt: 'Rotation douteuse', high_blur: 'Flou eleve', known_bibs_mismatch: 'Pas dans la liste' }
function reasonLabel(r) { return reasonLabels[r] || r }
function reasonBadge(r) {
  const m = { hallucination: 'bg-red-100 text-red-700', low_confidence: 'bg-amber-100 text-amber-700', fallback: 'bg-purple-100 text-purple-700', multi_bib: 'bg-blue-100 text-blue-700', high_blur: 'bg-gray-100 text-gray-600', known_bibs_mismatch: 'bg-orange-100 text-orange-700' }
  return m[r] || 'bg-gray-100 text-gray-600'
}

function diffBadge(d) {
  const m = { easy: 'bg-green-100 text-green-700', normal: 'bg-gray-100 text-gray-600', hard: 'bg-amber-100 text-amber-700', extreme: 'bg-red-100 text-red-700' }
  return m[d] || 'bg-gray-100 text-gray-600'
}

function modelStatusBadge(s) {
  const m = { training: 'bg-amber-100 text-amber-700', candidate: 'bg-blue-100 text-blue-700', validated: 'bg-green-100 text-green-700', production: 'bg-green-600 text-white', archived: 'bg-gray-100 text-gray-500' }
  return m[s] || 'bg-gray-100 text-gray-600'
}

function sessionStatusBadge(s) {
  const m = { pending: 'bg-gray-100 text-gray-600', running: 'bg-blue-100 text-blue-700', completed: 'bg-green-100 text-green-700', failed: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}

// ─── Init ───
onMounted(() => {
  loadDashboard()
  loadReview()
  loadGroundTruth()
  loadDatasets()
  loadModels()
  loadSessions()
})
</script>
