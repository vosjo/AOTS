<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <RouterLink
      to="/admin/users/"
      class="rounded-xl border border-slate-500 bg-slate-800 p-5 transition hover:border-sky-400 hover:bg-slate-700"
    >
      <h2 class="text-lg font-medium">Users</h2>
      <p class="mt-1 text-sm text-slate-300">Accounts, permissions, passwords</p>
    </RouterLink>
    <RouterLink
      to="/admin/projects/"
      class="rounded-xl border border-slate-500 bg-slate-800 p-5 transition hover:border-sky-400 hover:bg-slate-700"
    >
      <h2 class="text-lg font-medium">Projects</h2>
      <p class="mt-1 text-sm text-slate-300">Project settings and role assignments</p>
    </RouterLink>
    <RouterLink
      to="/admin/groups/"
      class="rounded-xl border border-slate-500 bg-slate-800 p-5 transition hover:border-sky-400 hover:bg-slate-700"
    >
      <h2 class="text-lg font-medium">Groups</h2>
      <p class="mt-1 text-sm text-slate-300">Django auth groups and permissions</p>
    </RouterLink>
    <RouterLink
      to="/admin/tokens/"
      class="rounded-xl border border-slate-500 bg-slate-800 p-5 transition hover:border-sky-400 hover:bg-slate-700"
    >
      <h2 class="text-lg font-medium">DRF tokens</h2>
      <p class="mt-1 text-sm text-slate-300">Create and revoke API tokens</p>
    </RouterLink>
    <RouterLink
      to="/admin/log/"
      class="rounded-xl border border-slate-500 bg-slate-800 p-5 transition hover:border-sky-400 hover:bg-slate-700"
    >
      <h2 class="text-lg font-medium">Admin log</h2>
      <p class="mt-1 text-sm text-slate-300">Read-only audit trail</p>
    </RouterLink>
  </div>
</template>
