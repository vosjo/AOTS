<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { TriangleAlert } from '@lucide/vue'
import AppButton from '@/components/AppButton.vue'
import { confirmDialogState, resolveConfirm } from '@/composables/useConfirm'

const cancelButton = ref<InstanceType<typeof AppButton> | null>(null)

watch(
  () => confirmDialogState.open,
  async (open) => {
    if (!open) return
    await nextTick()
    const el = cancelButton.value?.$el as HTMLElement | undefined
    el?.focus()
  },
)

function onBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    resolveConfirm(false)
  }
}
</script>

<template>
  <dialog
    v-if="confirmDialogState.open"
    open
    class="fixed inset-0 z-[60] m-0 flex items-center justify-center bg-aots-overlay p-4 w-full max-w-none h-full max-h-none"
    aria-modal="true"
    @click="onBackdropClick"
    @keydown.escape.prevent="resolveConfirm(false)"
  >
    <div
      class="aots-panel w-full max-w-md shadow-lg"
      role="alertdialog"
      :aria-labelledby="confirmDialogState.title ? 'confirm-dialog-title' : undefined"
      aria-describedby="confirm-dialog-message"
      @click.stop
    >
      <div class="flex items-start gap-3">
        <TriangleAlert
          v-if="confirmDialogState.destructive"
          class="mt-0.5 h-6 w-6 shrink-0 text-amber-400"
          aria-hidden="true"
        />
        <div class="min-w-0 flex-1">
          <h2 id="confirm-dialog-title" class="text-lg font-medium text-aots-strong">
            {{ confirmDialogState.title }}
          </h2>
          <p
            id="confirm-dialog-message"
            class="mt-2 text-sm leading-relaxed text-aots-muted whitespace-pre-wrap"
          >
            {{ confirmDialogState.message }}
          </p>
        </div>
      </div>

      <div class="mt-5 flex justify-end gap-2">
        <AppButton
          ref="cancelButton"
          variant="ghost"
          @click="resolveConfirm(false)"
        >
          {{ confirmDialogState.cancelLabel }}
        </AppButton>
        <AppButton
          :variant="confirmDialogState.destructive ? 'ghost-danger' : 'primary'"
          @click="resolveConfirm(true)"
        >
          {{ confirmDialogState.confirmLabel }}
        </AppButton>
      </div>
    </div>
  </dialog>
</template>
