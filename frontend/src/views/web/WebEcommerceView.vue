<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">E-commerce</h1>
      <p class="text-gray-500 text-sm">Gerez vos produits et suivez vos ventes</p>
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

    <!-- Products -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl mb-8">
      <div class="px-5 py-4 border-b border-gray-100/60 flex items-center justify-between">
        <h2 class="font-semibold text-gray-900">Produits</h2>
        <button @click="showCreateProduct = true" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-xs font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center gap-1">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          Nouveau produit
        </button>
      </div>

      <div v-if="!products.length" class="p-8 text-center text-gray-400 text-sm">
        Aucun produit. Creez vos premiers produits (ex: Pack Digital, Pack + Poster...).
      </div>

      <div v-else class="divide-y divide-gray-100/60">
        <div v-for="p in products" :key="p.id" class="px-5 py-4 flex items-center gap-4 hover:bg-white/40 transition">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 backdrop-blur-sm" :class="iconBg(p.icon)">
            <span class="text-lg">{{ iconEmoji(p.icon) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-gray-900 text-sm">{{ p.name }}</h3>
            <p class="text-xs text-gray-400 truncate">{{ p.description || 'Pas de description' }}</p>
          </div>
          <div class="text-right shrink-0">
            <p class="font-bold text-gray-900 text-sm">{{ p.default_price.toFixed(2) }} EUR</p>
            <p class="text-xs text-gray-400">prix par defaut</p>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button @click="startEditProduct(p)" class="text-gray-400 hover:text-blue-600 hover:bg-blue-50/50 p-1.5 rounded-lg transition">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            </button>
            <button @click="deleteProduct(p.id)" class="text-gray-400 hover:text-red-600 hover:bg-red-50/50 p-1.5 rounded-lg transition">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Clients -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl">
        <div class="px-5 py-4 border-b border-gray-100/60">
          <h2 class="font-semibold text-gray-900">Clients</h2>
        </div>
        <div class="p-6 text-center">
          <p class="text-3xl font-bold text-gray-900">{{ stats.total_customers }}</p>
          <p class="text-sm text-gray-400 mt-1">clients inscrits</p>
        </div>
      </div>

      <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl">
        <div class="px-5 py-4 border-b border-gray-100/60">
          <h2 class="font-semibold text-gray-900">Commandes recentes</h2>
        </div>
        <div class="p-6 text-center text-gray-400 text-sm">
          Les commandes apparaitront ici.
        </div>
      </div>
    </div>

    <!-- Create Product Modal -->
    <div v-if="showCreateProduct" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="bg-white/90 backdrop-blur-2xl border border-white/60 shadow-2xl rounded-3xl w-full max-w-md mx-4 p-6">
        <h2 class="text-lg font-semibold mb-4 text-gray-900">{{ editingProduct ? 'Modifier le produit' : 'Nouveau produit' }}</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
            <input v-model="productForm.name" type="text" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="Pack Photo Digital">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea v-model="productForm.description" rows="2" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition" placeholder="Toutes vos photos en haute definition..."></textarea>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Type</label>
              <select v-model="productForm.icon" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
                <option value="photos">Photos digitales</option>
                <option value="poster">Poster / Impression</option>
                <option value="book">Livre souvenir</option>
                <option value="frame">Cadre photo</option>
                <option value="usb">Cle USB</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Prix par defaut (EUR)</label>
              <input v-model.number="productForm.default_price" type="number" step="0.01" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showCreateProduct = false; editingProduct = null" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl text-sm transition">Annuler</button>
          <button @click="submitProduct" :disabled="!productForm.name" class="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-5 py-2 rounded-xl font-medium text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">
            {{ editingProduct ? 'Sauvegarder' : 'Creer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { webApi } from '../../api/events.js'
import { useToast } from '../../composables/useToast'
const toast = useToast()

const stats = ref({ published_events: 0, total_photos: 0, total_orders: 0, total_revenue: 0, total_customers: 0 })
const products = ref([])
const showCreateProduct = ref(false)
const editingProduct = ref(null)

const defaultProductForm = () => ({ name: '', description: '', icon: 'photos', default_price: 9.90 })
const productForm = ref(defaultProductForm())

const iconMap = { photos: '📸', poster: '🖼️', book: '📖', frame: '🪟', usb: '💾' }
const bgMap = { photos: 'bg-blue-100/80', poster: 'bg-gray-100/80', book: 'bg-gray-100/80', frame: 'bg-blue-100/80', usb: 'bg-gray-100/80' }
function iconEmoji(icon) { return iconMap[icon] || '📦' }
function iconBg(icon) { return bgMap[icon] || 'bg-gray-100/80' }

async function loadData() {
  try {
    const [statsRes, productsRes] = await Promise.all([
      webApi.stats(),
      webApi.listProducts(),
    ])
    stats.value = statsRes.data
    products.value = productsRes.data
  } catch (e) { console.error(e) }
}

function startEditProduct(p) {
  editingProduct.value = p.id
  productForm.value = { name: p.name, description: p.description || '', icon: p.icon, default_price: p.default_price }
  showCreateProduct.value = true
}

async function submitProduct() {
  try {
    if (editingProduct.value) {
      await webApi.updateProduct(editingProduct.value, productForm.value)
    } else {
      await webApi.createProduct(productForm.value)
    }
    showCreateProduct.value = false
    editingProduct.value = null
    productForm.value = defaultProductForm()
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

async function deleteProduct(id) {
  if (!confirm('Supprimer ce produit ?')) return
  try {
    await webApi.deleteProduct(id)
    await loadData()
  } catch (e) { toast.error(e.response?.data?.detail || e.message) }
}

onMounted(loadData)
</script>
