<script setup lang="ts">
import { computed } from 'vue'
import { AlertCircle, CheckCircle2, Info, TriangleAlert } from '@lucide/vue'
import { alertIconClass, alertPanelClass, type AlertKind } from '@/utils/alertStyles'

const props = withDefaults(
  defineProps<{
    kind?: AlertKind
    title?: string
    centered?: boolean
    showIcon?: boolean
  }>(),
  {
    kind: 'info',
    title: undefined,
    centered: false,
    showIcon: true,
  },
)

const icon = computed(() => {
  switch (props.kind) {
    case 'success':
      return CheckCircle2
    case 'warning':
      return TriangleAlert
    case 'error':
      return AlertCircle
    default:
      return Info
  }
})

const role = computed(() => (props.kind === 'error' || props.kind === 'warning' ? 'alert' : 'status'))
</script>

<template>
  <div
    :class="[alertPanelClass(kind), centered ? 'text-center' : '']"
    :role="role"
    aria-live="polite"
  >
    <div
      class="flex gap-3 items-start"
      :class="centered ? 'justify-center' : ''"
    >
      <component
        :is="icon"
        v-if="showIcon"
        class="w-5 h-5 shrink-0 mt-0.5"
        :class="alertIconClass(kind)"
      />
      <div
        class="min-w-0"
        :class="centered && showIcon ? 'text-left' : ''"
      >
        <p
          v-if="title"
          class="font-medium"
        >
          {{ title }}
        </p>
        <div :class="title ? 'mt-1.5 leading-relaxed opacity-90' : 'leading-relaxed'">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>
