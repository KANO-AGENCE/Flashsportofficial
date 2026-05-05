import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])
  const eventInfo = ref(null)

  const total = computed(() =>
    items.value.reduce((sum, item) => sum + item.price, 0)
  )

  const count = computed(() => items.value.length)

  function addPack(productId, productName, bibNumber, photoCount, price) {
    // Remove existing item for same bib + product
    items.value = items.value.filter(i => !(i.productId === productId && i.bibNumber === bibNumber))
    items.value.push({ productId, productName, bibNumber, photoCount, price })
  }

  function removeItem(index) {
    items.value.splice(index, 1)
  }

  function clear() {
    items.value = []
    eventInfo.value = null
  }

  function setEventInfo(info) {
    eventInfo.value = info
  }

  return { items, total, count, eventInfo, addPack, removeItem, clear, setEventInfo }
})
