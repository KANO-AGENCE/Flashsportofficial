<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Courses web</h1>
        <p class="text-gray-500 text-sm">Creez et parametrez vos courses pour le site vitrine</p>
      </div>
      <button @click="openCreate" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-xl font-medium text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Ajouter une course
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="!webEvents.length" class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl p-12 text-center">
      <svg class="w-16 h-16 text-gray-200 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><circle cx="12" cy="13" r="3"/></svg>
      <p class="text-gray-500 mb-2">Aucune course web</p>
      <p class="text-gray-400 text-sm">Cliquez sur "Ajouter une course" pour lier une course TRI au site vitrine.</p>
    </div>

    <!-- Course list -->
    <div v-else class="space-y-4">
      <div v-for="we in webEvents" :key="we.id" class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl overflow-hidden">
        <div class="p-5 flex items-start gap-5">
          <!-- Cover -->
          <div class="w-32 h-24 rounded-xl bg-gray-100/80 overflow-hidden shrink-0 relative group cursor-pointer">
            <img v-if="we.cover_image" :src="we.cover_image" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-300">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
            </div>
            <label class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center cursor-pointer rounded-xl">
              <span class="text-white text-xs font-medium">Changer la photo</span>
              <input type="file" accept="image/*" class="hidden" @change="uploadCover(we.id, $event)" />
            </label>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="font-bold text-gray-900 text-lg truncate">{{ we.event_name }}</h3>
              <span v-if="we.is_published" class="text-xs bg-green-100/80 text-green-700 px-2 py-0.5 rounded-full font-medium backdrop-blur-sm">En ligne</span>
              <span v-else class="text-xs bg-gray-100/80 text-gray-600 px-2 py-0.5 rounded-full font-medium backdrop-blur-sm">Brouillon</span>
            </div>
            <p class="text-sm text-gray-500 mb-2">{{ we.event_date }} &middot; {{ we.photo_count || 0 }} photos &middot; {{ we.bib_count || 0 }} dossards</p>
            <p class="text-xs text-gray-400">/evenement/{{ we.slug }}</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 shrink-0">
            <button @click="openEdit(we)" class="bg-gray-100/80 hover:bg-gray-200/80 text-gray-700 px-4 py-2 rounded-xl text-xs font-medium transition backdrop-blur-sm">Parametrer</button>
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

    <!-- Create Modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white/90 backdrop-blur-2xl border border-white/60 shadow-2xl rounded-3xl w-full max-w-lg mx-4 p-6">
        <h2 class="text-lg font-semibold mb-4 text-gray-900">Nouvelle course web</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Lier a une course TRI</label>
            <select v-model="form.event_id" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
              <option :value="0" disabled>Selectionnez une course...</option>
              <option v-for="te in triEvents" :key="te.id" :value="te.id">{{ te.name }} ({{ te.date }})</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">URL slug</label>
            <div class="flex items-center gap-1">
              <span class="text-sm text-gray-400">/evenement/</span>
              <input v-model="form.slug" type="text" class="flex-1 px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="mon-evenement-2026">
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea v-model="form.description" rows="2" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="Description..."></textarea>
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-3">Les produits et prix se configurent ensuite via "Parametrer".</p>
        <div class="flex justify-end gap-3 mt-4">
          <button @click="showCreate = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl text-sm transition">Annuler</button>
          <button @click="submitCreate" :disabled="!form.event_id || !form.slug" class="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-5 py-2 rounded-xl font-medium text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">Creer</button>
        </div>
      </div>
    </div>

    <!-- Edit / Settings Modal -->
    <div v-if="showEdit" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center overflow-y-auto py-8">
      <div class="bg-white/90 backdrop-blur-2xl border border-white/60 shadow-2xl rounded-3xl w-full max-w-xl mx-4 p-6">
        <h2 class="text-lg font-semibold mb-4 text-gray-900">Parametrer — {{ editEventName }}</h2>

        <div class="space-y-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">URL slug</label>
            <div class="flex items-center gap-1">
              <span class="text-sm text-gray-400">/evenement/</span>
              <input v-model="editForm.slug" type="text" class="flex-1 px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea v-model="editForm.description" rows="2" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition"></textarea>
          </div>
        </div>

        <!-- Products for this course -->
        <div class="border-t border-gray-100/60 pt-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-gray-900 text-sm">Produits de cette course</h3>
          </div>

          <!-- Existing event products -->
          <div v-if="eventProducts.length" class="space-y-2 mb-4">
            <div v-for="ep in eventProducts" :key="ep.id" class="flex items-center gap-3 bg-gray-50/80 backdrop-blur-sm rounded-xl p-3 border border-gray-100/60">
              <div class="flex-1 min-w-0">
                <p class="font-medium text-gray-900 text-sm">{{ ep.product_name }}</p>
                <p class="text-xs text-gray-400">{{ ep.product_description }}</p>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <input v-model.number="ep.price" type="number" step="0.01" class="w-20 px-2 py-1.5 bg-white/70 border border-gray-200/60 rounded-xl text-sm text-right focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 outline-none transition" @change="updateEventProduct(ep)">
                <span class="text-xs text-gray-400">EUR</span>
                <label class="flex items-center gap-1 text-xs cursor-pointer">
                  <input type="checkbox" v-model="ep.is_featured" @change="updateEventProduct(ep)" class="rounded">
                  <span class="text-gray-500">Vedette</span>
                </label>
                <button @click="removeEventProduct(ep.id)" class="text-red-400 hover:text-red-600 hover:bg-red-50/50 p-1 rounded-lg transition">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-gray-400 mb-4">Aucun produit associe. Ajoutez-en depuis la liste ci-dessous.</div>

          <!-- Add product -->
          <div v-if="availableProducts.length" class="flex items-center gap-2">
            <select v-model="addProductId" class="flex-1 px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
              <option :value="0" disabled>Ajouter un produit...</option>
              <option v-for="p in availableProducts" :key="p.id" :value="p.id">{{ p.name }} ({{ p.default_price }} EUR)</option>
            </select>
            <button @click="addProduct" :disabled="!addProductId" class="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-4 py-2 rounded-xl text-xs font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">Ajouter</button>
          </div>
          <p v-else class="text-xs text-gray-400 mt-2">
            Tous les produits sont ajoutes. <router-link to="/web/ecommerce" class="text-blue-600 hover:underline">Creer un nouveau produit</router-link>
          </p>
        </div>

        <div class="flex justify-end gap-3 mt-6 border-t border-gray-100/60 pt-4">
          <button @click="showEdit = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl text-sm transition">Fermer</button>
          <button @click="submitEdit" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-xl font-medium text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">Sauvegarder</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { webApi } from '../../api/events.js'
import api from '../../api/client.js'
import { useToast } from '../../composables/useToast'
const toast = useToast()

const webEvents = ref([])
const triEvents = ref([])
const allProducts = ref([])
const showCreate = ref(false)
const showEdit = ref(false)
const editingId = ref(null)
const editEventName = ref('')
const eventProducts = ref([])
const addProductId = ref(0)

const defaultForm = () => ({ event_id: 0, slug: '', description: '' })
const form = ref(defaultForm())
const editForm = ref({ slug: '', description: '' })

const availableProducts = computed(() => {
  const usedIds = eventProducts.value.map(ep => ep.product_id)
  return allProducts.value.filter(p => p.is_active && !usedIds.includes(p.id))
})

async function loadData() {
  try {
    const res = await webApi.listWebEvents()
    webEvents.value = res.data
  } catch (e) { console.error(e) }
}

async function loadTriEvents() {
  try {
    const res = await api.get('/web/admin/tri-events')
    triEvents.value = res.data
  } catch (e) { console.error(e) }
}

async function loadProducts() {
  try {
    const res = await webApi.listProducts()
    allProducts.value = res.data
  } catch (e) { console.error(e) }
}

async function loadEventProducts(webEventId) {
  try {
    const res = await webApi.listEventProducts(webEventId)
    eventProducts.value = res.data
  } catch (e) { console.error(e) }
}

function openCreate() {
  form.value = defaultForm()
  loadTriEvents()
  showCreate.value = true
}

watch(() => form.value.event_id, (id) => {
  const te = triEvents.value.find(e => e.id === id)
  if (te) form.value.slug = te.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
})

async function submitCreate() {
  try {
    await api.post('/web/admin/events', form.value)
    showCreate.value = false
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function openEdit(we) {
  editingId.value = we.id
  editEventName.value = we.event_name
  editForm.value = { slug: we.slug, description: we.description || '' }
  await Promise.all([loadProducts(), loadEventProducts(we.id)])
  addProductId.value = 0
  showEdit.value = true
}

async function submitEdit() {
  try {
    await webApi.updateWebEvent(editingId.value, editForm.value)
    showEdit.value = false
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function addProduct() {
  if (!addProductId.value) return
  const product = allProducts.value.find(p => p.id === addProductId.value)
  try {
    await webApi.addEventProduct(editingId.value, {
      product_id: addProductId.value,
      price: product?.default_price || 9.90,
      is_featured: eventProducts.value.length === 0,
    })
    addProductId.value = 0
    await loadEventProducts(editingId.value)
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function updateEventProduct(ep) {
  try {
    await webApi.updateEventProduct(ep.id, { price: ep.price, is_featured: ep.is_featured })
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function removeEventProduct(wepId) {
  try {
    await webApi.deleteEventProduct(wepId)
    await loadEventProducts(editingId.value)
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
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
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function deleteWebEvent(id) {
  if (!confirm('Supprimer cette course web ?')) return
  try {
    await api.delete(`/web/admin/events/${id}`)
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

onMounted(loadData)
</script>
