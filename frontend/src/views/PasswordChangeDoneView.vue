<script setup lang="ts">
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
</script>

<template>
  <div class="max-w-sm mx-auto mt-16 space-y-4">
    <h1 class="text-2xl font-semibold">Password changed</h1>
    <AppAlert kind="success" title="All set">
      Your password has been updated.
    </AppAlert>
    <AppButton variant="link" to="/users/you/">Back to profile</AppButton>
  </div>
</template>
