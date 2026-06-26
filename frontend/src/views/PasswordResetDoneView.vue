<script setup lang="ts">
import AppAlert from '@/components/AppAlert.vue'
import AppButton from '@/components/AppButton.vue'
</script>

<template>
  <div class="max-w-sm mx-auto mt-16 space-y-4">
    <h1 class="text-2xl font-semibold">Check your email</h1>
    <AppAlert kind="info" title="Reset link sent">
      If an account exists with that email address, you will receive a password reset link shortly.
      The link is valid for a limited time.
    </AppAlert>
    <AppButton variant="link" to="/accounts/login/">Back to login</AppButton>
  </div>
</template>
