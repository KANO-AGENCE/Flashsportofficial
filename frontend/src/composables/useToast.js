import { ref } from 'vue'

const toasts = ref([])
let nextId = 0

function addToast(message, type = 'info', duration = 4000) {
  const id = nextId++
  toasts.value.push({ id, message, type })
  if (duration > 0) {
    setTimeout(() => removeToast(id), duration)
  }
}

function removeToast(id) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

export function useToast() {
  return {
    toasts,
    removeToast,
    success: (msg) => addToast(msg, 'success'),
    error: (msg) => addToast(msg, 'error', 6000),
    info: (msg) => addToast(msg, 'info'),
    warn: (msg) => addToast(msg, 'warn', 5000),
  }
}
