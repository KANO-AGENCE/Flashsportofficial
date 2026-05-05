<template>
  <div class="max-w-3xl mx-auto px-4 py-12">
    <h1 class="text-2xl font-bold text-[var(--navy)] mb-8">Votre panier</h1>

    <!-- Empty cart -->
    <div v-if="!cart.items.length" class="text-center py-16">
      <svg class="w-16 h-16 text-[var(--slate)]/30 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z"/></svg>
      <p class="text-[var(--slate)]">Votre panier est vide.</p>
      <router-link to="/" class="text-[var(--turquoise)] font-semibold mt-4 inline-block">Parcourir les evenements</router-link>
    </div>

    <!-- Cart items -->
    <div v-else>
      <div class="space-y-3 mb-8">
        <div
          v-for="(item, idx) in cart.items"
          :key="idx"
          class="bg-white rounded-xl p-4 flex items-center justify-between shadow-sm border border-[var(--beige)]"
        >
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-lg bg-[var(--turquoise)]/10 flex items-center justify-center text-xl">
              📸
            </div>
            <div>
              <p class="font-semibold text-[var(--navy)] text-sm">{{ item.productName }}</p>
              <p class="text-xs text-[var(--slate)]">Dossard #{{ item.bibNumber }} &middot; {{ item.photoCount }} photos</p>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <span class="font-bold text-[var(--navy)]">{{ item.price.toFixed(2) }}&euro;</span>
            <button @click="cart.removeItem(idx)" class="text-red-400 hover:text-red-600 transition">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Total + checkout -->
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-[var(--beige)]">
        <div class="flex items-center justify-between mb-6">
          <span class="text-lg font-bold text-[var(--navy)]">Total</span>
          <span class="text-2xl font-bold text-[var(--turquoise)]">{{ cart.total.toFixed(2) }}&euro;</span>
        </div>

        <div class="space-y-3 mb-6">
          <input v-model="email" type="email" placeholder="Votre email" class="w-full px-4 py-3 border-2 border-[var(--beige)] rounded-xl focus:outline-none focus:border-[var(--turquoise)] transition text-sm" />
          <div class="grid grid-cols-2 gap-3">
            <input v-model="firstName" type="text" placeholder="Prenom" class="px-4 py-3 border-2 border-[var(--beige)] rounded-xl focus:outline-none focus:border-[var(--turquoise)] transition text-sm" />
            <input v-model="lastName" type="text" placeholder="Nom" class="px-4 py-3 border-2 border-[var(--beige)] rounded-xl focus:outline-none focus:border-[var(--turquoise)] transition text-sm" />
          </div>
        </div>

        <button
          @click="checkout"
          :disabled="!email || checking"
          class="w-full bg-[var(--turquoise)] hover:bg-[var(--turquoise-hover)] disabled:opacity-40 text-white py-4 rounded-xl font-bold text-lg transition flex items-center justify-center gap-2"
        >
          <svg v-if="checking" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
          Commander
        </button>

        <p class="text-xs text-center text-[var(--slate)] mt-4 flex items-center justify-center gap-1">
          <svg class="w-3.5 h-3.5 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/></svg>
          Paiement securise — Vos donnees sont protegees
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart.js'
import { webApi } from '../api/web.js'
import { useToast } from '../composables/useToast'

const cart = useCartStore()
const router = useRouter()
const toast = useToast()

const email = ref('')
const firstName = ref('')
const lastName = ref('')
const checking = ref(false)

async function checkout() {
  if (!email.value) return
  checking.value = true
  try {
    const items = cart.items.map(i => ({
      product_id: i.productId,
      bib_number: i.bibNumber || null,
    }))
    await webApi.checkout({
      email: email.value,
      first_name: firstName.value,
      last_name: lastName.value,
      items,
      web_event_id: cart.eventInfo?.web_event_id || 0,
    })
    cart.clear()
    router.push('/confirmation')
  } catch (e) {
    toast.error('Erreur lors de la commande: ' + (e.response?.data?.detail || e.message))
  } finally {
    checking.value = false
  }
}
</script>
