<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { buttonClasses, type AppButtonSize, type AppButtonVariant } from '@/utils/buttonStyles'

const props = withDefaults(
  defineProps<{
    variant?: AppButtonVariant
    size?: AppButtonSize
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    to?: string | Record<string, unknown>
    href?: string
    download?: string
    title?: string
    class?: string
  }>(),
  {
    variant: 'secondary',
    size: 'md',
    type: 'button',
    disabled: false,
    class: '',
  },
)

const tag = computed(() => {
  if (props.to) return RouterLink
  if (props.href) return 'a'
  return 'button'
})

const classes = computed(() => buttonClasses(props.variant, props.size, props.class))

const isDisabled = computed(() => props.disabled && tag.value === 'button')
</script>

<template>
  <component
    :is="tag"
    :class="classes"
    :disabled="isDisabled ? true : undefined"
    :type="tag === 'button' ? type : undefined"
    :to="to"
    :href="href"
    :download="download"
    :title="title"
    :aria-disabled="disabled && tag !== 'button' ? true : undefined"
  >
    <slot />
  </component>
</template>
