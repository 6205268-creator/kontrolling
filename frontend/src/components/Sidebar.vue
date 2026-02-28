<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <LayoutDashboard class="brand-icon" aria-hidden />
      <span class="brand-text">Контроллинг-СТ</span>
    </div>
    <nav class="sidebar-nav" aria-label="Основное меню">
      <router-link to="/dashboard" class="nav-item">
        <LayoutDashboard class="nav-icon" aria-hidden />
        <span>Dashboard</span>
      </router-link>

      <router-link to="/land-plots" class="nav-item">
        <MapPin class="nav-icon" aria-hidden />
        <span>Участки</span>
      </router-link>

      <router-link to="/owners" class="nav-item">
        <Users class="nav-icon" aria-hidden />
        <span>Владельцы</span>
      </router-link>

      <router-link to="/accruals" class="nav-item">
        <Wallet class="nav-icon" aria-hidden />
        <span>Начисления</span>
      </router-link>

      <router-link to="/payments" class="nav-item">
        <CreditCard class="nav-icon" aria-hidden />
        <span>Платежи</span>
      </router-link>

      <router-link to="/expenses" class="nav-item">
        <TrendingDown class="nav-icon" aria-hidden />
        <span>Расходы</span>
      </router-link>

      <router-link to="/meters" class="nav-item">
        <Gauge class="nav-icon" aria-hidden />
        <span>Счётчики</span>
      </router-link>

      <router-link to="/reports" class="nav-item">
        <FileText class="nav-icon" aria-hidden />
        <span>Отчёты</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import {
  LayoutDashboard,
  MapPin,
  Users,
  Wallet,
  CreditCard,
  TrendingDown,
  Gauge,
  FileText,
} from 'lucide-vue-next';
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 272px;
  z-index: 50;
  background: var(--color-sidebar);
  padding: 1.25rem 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 1.25rem 0.5rem;
  margin-bottom: 0.25rem;
}

.brand-icon {
  width: 28px;
  height: 28px;
  color: var(--color-sidebar-accent);
  flex-shrink: 0;
}

.brand-text {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-text-inverse);
  letter-spacing: -0.02em;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.75rem 1.25rem;
  margin: 0 0.5rem;
  color: var(--color-sidebar-muted);
  text-decoration: none;
  transition: background var(--transition-base), color var(--transition-base);
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
  box-shadow: inset 4px 0 0 var(--color-sidebar-accent);
}

.nav-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  opacity: 0.9;
}

.nav-item.router-link-active .nav-icon {
  color: var(--color-sidebar-accent);
}
</style>
