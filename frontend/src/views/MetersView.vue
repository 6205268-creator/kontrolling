<template>
  <div class="placeholder-view">
    <div class="placeholder-icon-wrap">
      <Gauge class="placeholder-icon" aria-hidden />
    </div>
    <h1>Счётчики</h1>
    <p>Приборы учёта (в разработке)</p>
  </div>
</template>

<script setup lang="ts">
import { Gauge } from 'lucide-vue-next';
</script>

<style scoped>
.placeholder-view {
  padding: 2.5rem;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  text-align: center;
  max-width: 420px;
  margin: 0 auto;
}

.placeholder-icon-wrap {
  margin-bottom: 1rem;
}

.placeholder-icon {
  width: 3rem;
  height: 3rem;
  color: var(--color-primary);
  opacity: 0.9;
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
