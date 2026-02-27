<template>
  <div class="main-layout">
    <Sidebar />
    
    <div class="main-content">
      <header class="header">
        <h1 class="header-title">Controlling</h1>
        
        <div class="header-right">
          <span v-if="authStore.user" class="user-info">
            {{ authStore.user.username }} ({{ authStore.user.role }})
          </span>
          <button class="logout-button" @click="handleLogout">
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
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import Sidebar from '@/components/Sidebar.vue';

const router = useRouter();
const authStore = useAuthStore();

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
  margin-left: 260px;
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

.user-info {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.logout-button {
  padding: 0.5rem 1rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.logout-button:hover {
  background: var(--color-bg);
  border-color: var(--color-text-muted);
}

.content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}
</style>
