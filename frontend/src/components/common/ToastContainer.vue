<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg backdrop-blur-xl border cursor-pointer"
          :class="styles[toast.type]"
          @click="removeToast(toast.id)"
        >
          <span class="text-lg leading-none mt-0.5">{{ icons[toast.type] }}</span>
          <p class="text-sm font-medium flex-1">{{ toast.message }}</p>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '../../composables/useToast'

const { toasts, removeToast } = useToast()

const styles = {
  success: 'bg-emerald-50/90 border-emerald-200 text-emerald-800',
  error: 'bg-red-50/90 border-red-200 text-red-800',
  info: 'bg-blue-50/90 border-blue-200 text-blue-800',
  warn: 'bg-amber-50/90 border-amber-200 text-amber-800',
}

const icons = {
  success: '\u2705',
  error: '\u274C',
  info: '\u2139\uFE0F',
  warn: '\u26A0\uFE0F',
}
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
