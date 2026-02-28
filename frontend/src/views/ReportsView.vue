<template>
  <div class="reports-view">
    <h1>Отчёты</h1>
    <nav class="reports-nav" aria-label="Отчёты">
      <router-link to="/reports/debtors" class="report-link">
        <UserX class="report-link-icon" aria-hidden />
        Отчёт по должникам
      </router-link>
      <router-link to="/reports/cash-flow" class="report-link">
        <TrendingUp class="report-link-icon" aria-hidden />
        Движение средств
      </router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { UserX, TrendingUp } from 'lucide-vue-next';
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
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  text-decoration: none;
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
  transition: background var(--transition-base), color var(--transition-base), border-color var(--transition-base);
}

.report-link:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.report-link.router-link-active {
  background: linear-gradient(180deg, #14b8a6 0%, var(--color-primary) 100%);
  color: white;
  border-color: transparent;
}

.report-link-icon {
  width: 1.25rem;
  height: 1.25rem;
  opacity: 0.9;
}
</style>
