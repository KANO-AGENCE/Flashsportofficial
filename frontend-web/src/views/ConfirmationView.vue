<template>
  <div class="max-w-xl mx-auto px-4 py-20 text-center">
    <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
      <svg class="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
      </svg>
    </div>
    <h1 class="text-3xl font-bold text-[var(--navy)] mb-3">Merci pour votre commande !</h1>
    <p class="text-[var(--slate)] mb-8">
      Votre commande a bien ete enregistree. Vous recevrez un email avec le lien de telechargement
      une fois le paiement confirme.
    </p>
    <router-link to="/" class="bg-[var(--turquoise)] hover:bg-[var(--turquoise-hover)] text-white px-8 py-3 rounded-xl font-semibold transition inline-block">
      Retour a l'accueil
    </router-link>
  </div>
</template>
