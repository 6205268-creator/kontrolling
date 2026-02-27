<template>
  <aside class="sidebar">
    <nav class="sidebar-nav">
      <router-link to="/dashboard" class="nav-item">
        <span class="nav-icon">📊</span>
        <span>Dashboard</span>
      </router-link>
      
      <router-link to="/land-plots" class="nav-item">
        <span class="nav-icon">🏞️</span>
        <span>Участки</span>
      </router-link>
      
      <router-link to="/owners" class="nav-item">
        <span class="nav-icon">👥</span>
        <span>Владельцы</span>
      </router-link>
      
      <router-link to="/accruals" class="nav-item">
        <span class="nav-icon">💰</span>
        <span>Начисления</span>
      </router-link>
      
      <router-link to="/payments" class="nav-item">
        <span class="nav-icon">💳</span>
        <span>Платежи</span>
      </router-link>
      
      <router-link to="/expenses" class="nav-item">
        <span class="nav-icon">📉</span>
        <span>Расходы</span>
      </router-link>
      
      <router-link to="/meters" class="nav-item">
        <span class="nav-icon">📏</span>
        <span>Счётчики</span>
      </router-link>
      
      <router-link to="/reports" class="nav-item">
        <span class="nav-icon">📋</span>
        <span>Отчёты</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 260px;
  background: var(--color-sidebar);
  padding: 1.5rem 0;
  overflow-y: auto;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  margin: 0 0.5rem;
  color: #94a3b8;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  border-radius: var(--radius-md);
}

.nav-item:hover {
  background: var(--color-sidebar-hover);
  color: var(--color-text-inverse);
}

.nav-item.router-link-active {
  background: var(--color-sidebar-active);
  color: var(--color-text-inverse);
  box-shadow: inset 3px 0 0 var(--color-sidebar-accent);
}

.nav-icon {
  font-size: 1.125rem;
  opacity: 0.9;
}
</style>
