<template>
  <div class="reports-view">
    <h1>Отчёты</h1>
    <nav class="reports-nav">
      <router-link to="/reports/debtors" class="report-link">
        Отчёт по должникам
      </router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.reports-view {
  padding: 1.5rem;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.reports-view h1 {
  margin: 0 0 1rem 0;
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.reports-nav {
  margin-bottom: 1.25rem;
}

.report-link {
  display: inline-block;
  padding: 0.625rem 1rem;
  background: var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  text-decoration: none;
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
  transition: background 0.2s, color 0.2s;
}

.report-link:hover {
  background: #cbd5e1;
}

.report-link.router-link-active {
  background: var(--color-primary);
  color: white;
}
</style>
