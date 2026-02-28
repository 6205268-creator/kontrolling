<template>
  <div class="dashboard">
    <div class="welcome-card">
      <h2 class="welcome-title">Добро пожаловать в Контроллинг-СТ</h2>
      <p class="welcome-desc">Система учёта хозяйственной деятельности садоводческих товариществ</p>
      <p v-if="authStore.cooperativeName" class="current-cooperative">
        Текущее товарищество: <strong>{{ authStore.cooperativeName }}</strong>
      </p>

      <div class="features-grid">
        <router-link to="/land-plots" class="feature-item">
          <MapPin class="feature-icon" aria-hidden />
          <h3>Участки</h3>
          <p>Земельные участки и владельцы</p>
        </router-link>
        <router-link to="/owners" class="feature-item">
          <Users class="feature-icon" aria-hidden />
          <h3>Владельцы</h3>
          <p>Физ. и юр. лица</p>
        </router-link>
        <router-link to="/accruals" class="feature-item">
          <Wallet class="feature-icon" aria-hidden />
          <h3>Начисления</h3>
          <p>Взносы по участкам</p>
        </router-link>
        <router-link to="/payments" class="feature-item">
          <CreditCard class="feature-icon" aria-hidden />
          <h3>Платежи</h3>
          <p>Регистрация платежей</p>
        </router-link>
        <router-link to="/expenses" class="feature-item">
          <TrendingDown class="feature-icon" aria-hidden />
          <h3>Расходы</h3>
          <p>Учёт расходов СТ</p>
        </router-link>
        <router-link to="/meters" class="feature-item">
          <Gauge class="feature-icon" aria-hidden />
          <h3>Счётчики</h3>
          <p>Приборы учёта</p>
        </router-link>
        <router-link to="/reports" class="feature-item">
          <BarChart3 class="feature-icon" aria-hidden />
          <h3>Отчёты</h3>
          <p>Должники и движение средств</p>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  MapPin,
  Users,
  Wallet,
  CreditCard,
  TrendingDown,
  Gauge,
  BarChart3,
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.welcome-card {
  background: var(--color-bg-card);
  padding: 2rem;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-border);
}

.welcome-title {
  margin: 0 0 0.5rem 0;
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.welcome-desc {
  margin: 0 0 0.5rem 0;
  font-size: var(--text-base);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
}

.current-cooperative {
  margin: 0 0 2rem 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.current-cooperative strong {
  color: var(--color-primary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

.feature-item {
  padding: 1.5rem 1.25rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  text-align: center;
  transition: border-color var(--transition-base), box-shadow var(--transition-base), transform var(--transition-fast);
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.feature-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}

.feature-icon {
  width: 2.25rem;
  height: 2.25rem;
  color: var(--color-primary);
  flex-shrink: 0;
}

.feature-item h3 {
  margin: 0;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.feature-item p {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-tight);
}
</style>
