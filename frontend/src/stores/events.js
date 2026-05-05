import { defineStore } from 'pinia'
import { ref } from 'vue'
import { eventsApi } from '../api/events'

export const useEventsStore = defineStore('events', () => {
  const events = ref([])
  const currentEvent = ref(null)
  const loading = ref(false)

  async function fetchEvents() {
    loading.value = true
    try {
      const res = await eventsApi.list()
      events.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchEvent(id) {
    loading.value = true
    try {
      const res = await eventsApi.get(id)
      currentEvent.value = res.data
    } finally {
      loading.value = false
    }
  }

  return { events, currentEvent, loading, fetchEvents, fetchEvent }
})
