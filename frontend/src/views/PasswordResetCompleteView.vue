<script setup lang="ts">
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
</script>

<template>
  <div class="max-w-sm mx-auto mt-16 space-y-4">
    <h1 class="text-2xl font-semibold">Password updated</h1>
    <AppAlert kind="success" title="All set">
      Your password has been reset. You can now sign in with your new password.
    </AppAlert>
    <AppButton variant="primary" to="/accounts/login/">Sign in</AppButton>
  </div>
</template>
