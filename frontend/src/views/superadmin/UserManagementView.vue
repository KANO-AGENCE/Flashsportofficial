<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Utilisateurs</h1>
        <p class="text-gray-500 mt-1">Gestion des acces et modules</p>
      </div>
      <button @click="showCreate = true" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">
        + Nouvel utilisateur
      </button>
    </div>

    <!-- User list -->
    <div class="bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg shadow-black/5 rounded-2xl overflow-hidden">
      <table class="w-full">
        <thead class="border-b border-gray-100/60">
          <tr class="bg-white/30">
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Utilisateur</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Role</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Modules</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Statut</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100/60">
          <tr v-for="u in users" :key="u.id" class="hover:bg-white/40 transition">
            <td class="px-4 py-3">
              <p class="font-medium text-gray-900">{{ u.first_name }} {{ u.last_name }}</p>
              <p class="text-sm text-gray-400">{{ u.email }}</p>
            </td>
            <td class="px-4 py-3">
              <select :value="u.role" @change="updateRole(u.id, $event.target.value)" class="text-sm bg-white/50 border border-gray-200/60 rounded-xl px-2 py-1 backdrop-blur-sm outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition">
                <option value="SUPERADMIN">Super Admin</option>
                <option value="ADMIN">Admin</option>
                <option value="POSTE_TRI">Poste Tri</option>
              </select>
            </td>
            <td class="px-4 py-3">
              <div class="flex gap-1">
                <label v-for="mod in ['TRI', 'WEB', 'MAILING']" :key="mod" class="flex items-center gap-1">
                  <input type="checkbox" :checked="u.modules?.includes(mod)" @change="toggleModule(u, mod)" class="rounded">
                  <span class="text-xs text-gray-600">{{ mod }}</span>
                </label>
              </div>
            </td>
            <td class="px-4 py-3">
              <span :class="u.is_active ? 'bg-green-100/80 text-green-700' : 'bg-red-100/80 text-red-700'" class="text-xs font-medium px-2 py-1 rounded-full backdrop-blur-sm">
                {{ u.is_active ? 'Actif' : 'Inactif' }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <button @click="toggleActive(u)" class="text-gray-400 hover:text-gray-600 hover:bg-white/50 px-2 py-1 rounded-lg text-sm transition">
                {{ u.is_active ? 'Desactiver' : 'Activer' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showCreate = false">
      <div class="bg-white/90 backdrop-blur-2xl border border-white/60 shadow-2xl rounded-3xl w-full max-w-md mx-4 p-6">
        <h2 class="text-lg font-semibold mb-4 text-gray-900">Nouvel utilisateur</h2>
        <form @submit.prevent="createUser" class="space-y-3">
          <input v-model="newUser.email" type="email" required placeholder="Email" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
          <input v-model="newUser.password" type="password" required placeholder="Mot de passe" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
          <div class="grid grid-cols-2 gap-3">
            <input v-model="newUser.first_name" placeholder="Prenom" class="px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
            <input v-model="newUser.last_name" placeholder="Nom" class="px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
          </div>
          <select v-model="newUser.role" class="w-full px-3 py-2 bg-white/50 border border-gray-200/60 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 backdrop-blur-sm outline-none transition">
            <option value="POSTE_TRI">Poste Tri</option>
            <option value="ADMIN">Admin</option>
            <option value="SUPERADMIN">Super Admin</option>
          </select>
          <div class="flex justify-end gap-3 mt-4">
            <button type="button" @click="showCreate = false" class="px-4 py-2 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-xl transition">Annuler</button>
            <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all">Creer</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/client'

const users = ref([])
const showCreate = ref(false)
const newUser = ref({ email: '', password: '', first_name: '', last_name: '', role: 'POSTE_TRI' })

async function loadUsers() {
  const res = await api.get('/users')
  users.value = res.data
}

async function createUser() {
  await api.post('/users', newUser.value)
  showCreate.value = false
  newUser.value = { email: '', password: '', first_name: '', last_name: '', role: 'POSTE_TRI' }
  await loadUsers()
}

async function updateRole(userId, role) {
  await api.put(`/users/${userId}`, { role })
  await loadUsers()
}

async function toggleModule(user, mod) {
  const mods = [...(user.modules || [])]
  const idx = mods.indexOf(mod)
  if (idx >= 0) mods.splice(idx, 1)
  else mods.push(mod)
  await api.put(`/users/${user.id}`, { modules: mods })
  await loadUsers()
}

async function toggleActive(user) {
  await api.put(`/users/${user.id}`, { is_active: !user.is_active })
  await loadUsers()
}

onMounted(loadUsers)
</script>
