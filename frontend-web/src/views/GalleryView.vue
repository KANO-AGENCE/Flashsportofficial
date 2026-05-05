<template>
  <div v-if="loading" class="text-center py-20">
    <div class="inline-block w-8 h-8 border-4 border-[var(--turquoise)] border-t-transparent rounded-full animate-spin"></div>
  </div>

  <div v-else>
    <!-- Header -->
    <section class="bg-gradient-to-r from-[var(--navy)] to-[var(--slate)] text-white py-8">
      <div class="max-w-6xl mx-auto px-4">
        <router-link :to="`/evenement/${slug}`" class="text-white/60 hover:text-white text-sm mb-3 inline-flex items-center gap-1 transition">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          Retour a la recherche
        </router-link>
        <h1 class="text-2xl sm:text-3xl font-bold mt-1">Dossard #{{ bib }}</h1>
        <p v-if="gallery" class="text-white/60 mt-1">{{ gallery.photo_count }} photo(s) trouvee(s)</p>
      </div>
    </section>

    <!-- No results -->
    <section v-if="gallery && !gallery.photos.length" class="max-w-3xl mx-auto px-4 py-16 text-center">
      <svg class="w-16 h-16 text-[var(--slate)]/30 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <h2 class="text-xl font-bold text-[var(--navy)] mb-2">Aucune photo trouvee</h2>
      <p class="text-[var(--slate)] mb-6">Ce dossard n'a pas ete identifie sur cet evenement.</p>
      <router-link :to="`/evenement/${slug}`" class="bg-[var(--turquoise)] text-white px-6 py-3 rounded-xl font-semibold text-sm hover:bg-[var(--turquoise-hover)] transition">
        Essayer un autre numero
      </router-link>
    </section>

    <!-- Gallery with products -->
    <section v-if="gallery && gallery.photos.length" class="max-w-6xl mx-auto px-4 py-8">

      <!-- Products / Offers (pack featured first) -->
      <div v-if="gallery.products && gallery.products.length" class="mb-10">
        <h2 class="text-lg font-bold text-[var(--navy)] mb-4 text-center">Choisissez votre offre</h2>
        <div class="grid gap-4" :class="gallery.products.length === 1 ? 'max-w-sm mx-auto' : gallery.products.length === 2 ? 'grid-cols-1 sm:grid-cols-2 max-w-2xl mx-auto' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'">
          <div
            v-for="product in gallery.products"
            :key="product.id"
            :class="product.is_featured
              ? 'border-[var(--turquoise)] ring-2 ring-[var(--turquoise)]/20 scale-[1.02]'
              : 'border-[var(--beige)] hover:border-[var(--turquoise)]'"
            class="bg-white rounded-2xl p-6 text-center border-2 transition relative"
          >
            <div v-if="product.is_featured" class="absolute -top-3 left-1/2 -translate-x-1/2 bg-[var(--turquoise)] text-white text-xs font-bold px-4 py-1 rounded-full shadow-md">
              Recommande
            </div>
            <div class="text-3xl mb-1">{{ productIcon(product.icon) }}</div>
            <h3 class="font-bold text-[var(--navy)] text-lg">{{ product.name }}</h3>
            <p class="text-sm text-[var(--slate)] mt-1 mb-4">{{ product.description }}</p>
            <div class="text-3xl font-bold mb-4" :class="product.is_featured ? 'text-[var(--turquoise)]' : 'text-[var(--navy)]'">
              {{ product.price.toFixed(2) }}&euro;
            </div>
            <button
              @click="addProductToCart(product)"
              :class="isProductInCart(product.id)
                ? 'bg-[var(--turquoise)] hover:bg-[var(--turquoise-hover)]'
                : product.is_featured
                  ? 'bg-[var(--turquoise)] hover:bg-[var(--turquoise-hover)]'
                  : 'bg-[var(--navy)] hover:bg-[var(--slate)]'"
              class="text-white w-full py-3 rounded-xl font-semibold text-sm transition"
            >
              {{ isProductInCart(product.id) ? 'Ajoute au panier' : 'Ajouter au panier' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Photos grid -->
      <h2 class="text-lg font-bold text-[var(--navy)] mb-4">Vos {{ gallery.photo_count }} photos</h2>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
        <div
          v-for="photo in gallery.photos"
          :key="photo.id"
          class="photo-container bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow"
        >
          <div class="aspect-[3/4] bg-gray-100 relative">
            <img
              :src="photo.thumbnail_url"
              class="w-full h-full object-cover photo-protected"
              loading="lazy"
              draggable="false"
              @contextmenu.prevent
              @dragstart.prevent
            />
            <div class="absolute inset-0 z-10" @contextmenu.prevent></div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { webApi } from '../api/web.js'
import { useCartStore } from '../stores/cart.js'

const route = useRoute()
const cart = useCartStore()

const slug = route.params.slug
const bib = route.params.bib
const gallery = ref(null)
const loading = ref(true)

const iconMap = { photos: '📸', poster: '🖼️', book: '📖', frame: '🪟', usb: '💾' }
function productIcon(icon) { return iconMap[icon] || '📦' }

function isProductInCart(productId) {
  return cart.items.some(i => i.productId === productId && i.bibNumber === bib)
}

function addProductToCart(product) {
  if (isProductInCart(product.id)) return
  cart.addPack(product.id, product.name, bib, gallery.value.photo_count, product.price)
  cart.setEventInfo({ slug })
}

onMounted(async () => {
  try {
    const res = await webApi.searchBib(slug, bib)
    gallery.value = res.data
  } catch (e) {
    console.error('Failed to load gallery:', e)
  } finally {
    loading.value = false
  }
})
</script>
