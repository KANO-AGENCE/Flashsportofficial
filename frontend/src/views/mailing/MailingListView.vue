<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Mailing</h1>
        <p class="text-gray-500 text-sm">Creez et envoyez des emails a vos clients</p>
      </div>
      <button @click="openCreate" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-xs font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center gap-1">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Nouveau mailing
      </button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Mailings</p>
        <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.total_mailings }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Brouillons</p>
        <p class="text-3xl font-bold text-gray-500 mt-2">{{ stats.drafts }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Envoyes</p>
        <p class="text-3xl font-bold text-green-600 mt-2">{{ stats.sent }}</p>
      </div>
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-5">
        <p class="text-xs text-gray-400 uppercase tracking-wider">Clients</p>
        <p class="text-3xl font-bold text-blue-600 mt-2">{{ stats.total_customers }}</p>
      </div>
    </div>

    <!-- Mailings list -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl">
      <div class="px-5 py-4 border-b border-gray-100/60">
        <h2 class="font-semibold text-gray-900">Tous les mailings</h2>
      </div>

      <div v-if="!mailings.length" class="p-8 text-center text-gray-400 text-sm">
        Aucun mailing. Creez votre premier email.
      </div>

      <div v-else class="divide-y divide-gray-100/60">
        <div
          v-for="m in mailings"
          :key="m.id"
          class="px-5 py-4 hover:bg-white/40 transition cursor-pointer"
          @click="openEdit(m)"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 backdrop-blur-sm"
                :class="m.status === 'sent' ? 'bg-green-100/80' : 'bg-gray-100/80'">
                <svg v-if="m.status === 'sent'" class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                <svg v-else class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
              </div>
              <div class="min-w-0">
                <h3 class="font-semibold text-gray-900 text-sm truncate">{{ m.subject }}</h3>
                <p class="text-xs text-gray-400">
                  <span v-if="m.event_name">{{ m.event_name }}</span>
                  <span v-else>Tous les clients</span>
                  <span class="mx-1">&middot;</span>
                  {{ m.recipient_count }} destinataires
                </p>
              </div>
            </div>
            <div class="flex items-center gap-3 shrink-0">
              <span :class="statusClass(m.status)" class="text-xs font-medium px-2.5 py-1 rounded-full backdrop-blur-sm">
                {{ statusLabel(m.status) }}
              </span>
              <span class="text-xs text-gray-400">{{ formatDate(m.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white/90 backdrop-blur-2xl border border-white/60 shadow-2xl rounded-3xl w-full max-w-3xl mx-4 max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-100/60 flex items-center justify-between shrink-0">
          <h2 class="text-lg font-semibold text-gray-900">{{ editing ? 'Modifier le mailing' : 'Nouveau mailing' }}</h2>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600 hover:bg-white/50 p-1 rounded-xl transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Editor -->
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Sujet</label>
                <input v-model="form.subject" type="text" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="Vos photos sont disponibles !">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Segment</label>
                <select v-model="form.event_id" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
                  <option :value="null">Tous les clients</option>
                  <option v-for="ev in events" :key="ev.id" :value="ev.id">{{ ev.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Contenu</label>
                <textarea v-model="form.raw_content" rows="10" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm font-mono focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="Bonjour,&#10;&#10;Vos photos de course sont maintenant disponibles..."></textarea>
              </div>
            </div>

            <!-- Preview -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Apercu</label>
              <div class="border border-gray-200/60 rounded-xl overflow-hidden bg-gray-50/80 h-[380px]">
                <iframe v-if="editing && editing.id" :src="`/api/mailing/${editing.id}/preview`" class="w-full h-full border-0" ref="previewFrame"></iframe>
                <div v-else class="flex items-center justify-center h-full text-sm text-gray-400">
                  Sauvegardez pour voir l'apercu
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100/60 flex items-center justify-between shrink-0">
          <div class="flex items-center gap-2">
            <button v-if="editing" @click="deleteMailing" class="text-red-500 hover:text-red-700 hover:bg-red-50/50 text-sm px-3 py-2 rounded-xl transition">
              Supprimer
            </button>
          </div>
          <div class="flex items-center gap-3">
            <button @click="closeModal" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl text-sm transition">Annuler</button>
            <button v-if="editing && editing.status !== 'sent'" @click="sendMailing" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl font-medium text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
              Envoyer
            </button>
            <button @click="saveMailing" :disabled="!form.subject" class="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-5 py-2 rounded-xl font-medium text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">
              {{ editing ? 'Sauvegarder' : 'Creer' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { mailingApi } from '../../api/events'
import { useToast } from '../../composables/useToast'
const toast = useToast()

const stats = ref({ total_mailings: 0, drafts: 0, sent: 0, total_customers: 0, total_emails_sent: 0 })
const mailings = ref([])
const events = ref([])
const showModal = ref(false)
const editing = ref(null)
const form = ref({ subject: '', raw_content: '', event_id: null })

function statusLabel(s) {
  return { draft: 'Brouillon', ready: 'Pret', sent: 'Envoye' }[s] || s
}
function statusClass(s) {
  return {
    draft: 'bg-gray-100/80 text-gray-600',
    ready: 'bg-blue-100/80 text-blue-700',
    sent: 'bg-green-100/80 text-green-700',
  }[s] || 'bg-gray-100/80 text-gray-600'
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadData() {
  try {
    const [s, m, e] = await Promise.all([
      mailingApi.stats(),
      mailingApi.list(),
      mailingApi.listEvents(),
    ])
    stats.value = s.data
    mailings.value = m.data
    events.value = e.data
  } catch (e) { console.error(e) }
}

function openCreate() {
  editing.value = null
  form.value = { subject: '', raw_content: '', event_id: null }
  showModal.value = true
}

function openEdit(m) {
  editing.value = m
  form.value = { subject: m.subject, raw_content: m.raw_content || '', event_id: m.event_id }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editing.value = null
}

async function saveMailing() {
  try {
    if (editing.value) {
      await mailingApi.update(editing.value.id, form.value)
    } else {
      const res = await mailingApi.create(form.value)
      editing.value = res.data
    }
    await loadData()
    // Refresh preview if editing
    if (editing.value) {
      const fresh = await mailingApi.get(editing.value.id)
      editing.value = fresh.data
    }
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function sendMailing() {
  if (!editing.value) return
  if (!confirm(`Envoyer ce mailing a ${editing.value.recipient_count} destinataires ?`)) return
  try {
    await mailingApi.send(editing.value.id)
    closeModal()
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function deleteMailing() {
  if (!editing.value) return
  if (!confirm('Supprimer ce mailing ?')) return
  try {
    await mailingApi.delete(editing.value.id)
    closeModal()
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

onMounted(loadData)
</script>
