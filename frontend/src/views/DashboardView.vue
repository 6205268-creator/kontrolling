<template>
  <div class="dashboard">
    <div class="welcome-card">
      <h2 class="welcome-title">Добро пожаловать в Controlling</h2>
      <p class="welcome-desc">Система учёта хозяйственной деятельности садоводческих товариществ</p>

      <div class="features-grid">
        <router-link to="/land-plots" class="feature-item">
          <span class="feature-icon">📋</span>
          <h3>Участки</h3>
          <p>Земельные участки и владельцы</p>
        </router-link>
        <router-link to="/owners" class="feature-item">
          <span class="feature-icon">👥</span>
          <h3>Владельцы</h3>
          <p>Физ. и юр. лица</p>
        </router-link>
        <router-link to="/accruals" class="feature-item">
          <span class="feature-icon">💰</span>
          <h3>Начисления</h3>
          <p>Взносы по участкам</p>
        </router-link>
        <router-link to="/payments" class="feature-item">
          <span class="feature-icon">💳</span>
          <h3>Платежи</h3>
          <p>Регистрация платежей</p>
        </router-link>
        <router-link to="/expenses" class="feature-item">
          <span class="feature-icon">📊</span>
          <h3>Расходы</h3>
          <p>Учёт расходов СТ</p>
        </router-link>
        <router-link to="/meters" class="feature-item">
          <span class="feature-icon">⚡</span>
          <h3>Счётчики</h3>
          <p>Приборы учёта</p>
        </router-link>
        <router-link to="/reports" class="feature-item">
          <span class="feature-icon">📈</span>
          <h3>Отчёты</h3>
          <p>Должники и движение средств</p>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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
  letter-spacing: -0.02em;
}

.welcome-desc {
  margin: 0 0 2rem 0;
  font-size: var(--text-base);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.feature-item {
  padding: 1.25rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  text-align: center;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  text-decoration: none;
  color: inherit;
  display: block;
}

.feature-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.feature-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.75rem;
}

.feature-item h3 {
  margin: 0 0 0.25rem 0;
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
