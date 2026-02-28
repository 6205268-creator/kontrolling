<template>
  <div class="main-layout">
    <Sidebar />

    <div class="main-content">
      <header class="header">
        <h1 class="header-title">Контроллинг-СТ</h1>

        <div class="header-right">
          <span v-if="authStore.cooperativeName" class="cooperative-name" :title="authStore.cooperativeName">
            {{ authStore.cooperativeName }}
          </span>
          <span v-if="authStore.user" class="user-info">
            {{ authStore.user.username }} ({{ authStore.user.role }})
          </span>
          <button class="logout-button" type="button" @click="handleLogout" aria-label="Выйти">
            <LogOut class="logout-icon" aria-hidden />
            Выйти
          </button>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { LogOut } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import Sidebar from '@/components/Sidebar.vue';

const router = useRouter();
const authStore = useAuthStore();

onMounted(() => {
  if (authStore.cooperativeId && !authStore.cooperativeName) {
    authStore.loadCooperativeName();
  }
});

function handleLogout() {
  authStore.logout();
  router.push('/login');
}
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 272px;
  position: relative;
  z-index: 0;
  min-width: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.header-title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.cooperative-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-primary);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-info {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.logout-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
  cursor: pointer;
  transition: background var(--transition-base), border-color var(--transition-base);
}

.logout-button:hover {
  background: var(--color-bg);
  border-color: var(--color-text-muted);
}

.logout-icon {
  width: 1.125rem;
  height: 1.125rem;
  opacity: 0.85;
}

.content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  position: relative;
  pointer-events: auto;
  background: var(--color-bg);
}
</style>
