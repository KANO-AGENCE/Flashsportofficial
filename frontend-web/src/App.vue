<template>
  <!-- Navbar -->
  <nav class="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-[var(--beige)]">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-2">
        <div class="w-8 h-8 bg-[var(--turquoise)] rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><circle cx="12" cy="13" r="3"/></svg>
        </div>
        <span class="text-xl font-bold text-[var(--navy)]">Flash<span class="text-[var(--turquoise)]">Sport</span></span>
      </router-link>

      <div class="flex items-center gap-6">
        <router-link to="/" class="text-sm font-medium text-[var(--slate)] hover:text-[var(--turquoise)] transition hidden sm:block">Evenements</router-link>
        <router-link to="/panier" class="relative flex items-center gap-1 text-sm font-medium text-[var(--slate)] hover:text-[var(--turquoise)] transition">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z"/></svg>
          <span class="hidden sm:inline">Panier</span>
          <span v-if="cart.count" class="absolute -top-1 -right-3 bg-[var(--turquoise)] text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">{{ cart.count }}</span>
        </router-link>
      </div>
    </div>
  </nav>

  <ToastContainer />

  <!-- Content -->
  <main class="min-h-screen">
    <router-view />
  </main>

  <!-- Footer -->
  <footer class="bg-[var(--navy)] text-white/70 py-12 mt-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <h3 class="text-white font-bold text-lg mb-3">FlashSport</h3>
          <p class="text-sm">Vos souvenirs sportifs, disponibles instantanement.</p>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-3">Informations</h4>
          <ul class="space-y-2 text-sm">
            <li>FAQ</li>
            <li>Conditions generales</li>
            <li>Politique de confidentialite</li>
          </ul>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-3">Paiement securise</h4>
          <div class="flex items-center gap-3 mt-2">
            <div class="bg-white/10 px-3 py-1.5 rounded text-xs font-medium">Visa</div>
            <div class="bg-white/10 px-3 py-1.5 rounded text-xs font-medium">Mastercard</div>
            <div class="bg-white/10 px-3 py-1.5 rounded text-xs font-medium">Apple Pay</div>
          </div>
          <div class="flex items-center gap-2 mt-4 text-xs">
            <svg class="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/></svg>
            <span>SSL Securise</span>
          </div>
        </div>
      </div>
      <div class="border-t border-white/10 mt-8 pt-6 text-center text-xs text-white/40">
        FlashSport 2026. Tous droits reserves.
      </div>
    </div>
  </footer>
</template>

<script setup>
import { useCartStore } from './stores/cart.js'
import ToastContainer from './components/ToastContainer.vue'
const cart = useCartStore()
</script>
