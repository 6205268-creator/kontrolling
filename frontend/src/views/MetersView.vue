<template>
  <div class="placeholder-view">
    <h1>Счётчики</h1>
    <p>Приборы учёта (в разработке)</p>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.placeholder-view {
  padding: 1.5rem;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.placeholder-view h1 {
  margin: 0 0 0.5rem 0;
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.placeholder-view p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>
