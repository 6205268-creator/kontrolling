import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User, LoginCredentials } from '@/types';
import type { Cooperative } from '@/types';
import api from '@/services/api';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'));

  const savedUser = localStorage.getItem('user');
  const user = ref<User | null>(savedUser ? JSON.parse(savedUser) : null);

  const cooperativeName = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);
  const userRole = computed(() => user.value?.role);
  const cooperativeId = computed(() => user.value?.cooperative_id);

  async function loadCooperativeName(): Promise<void> {
    const id = user.value?.cooperative_id;
    if (!id) {
      cooperativeName.value = null;
      return;
    }
    try {
      const { data } = await api.get<Cooperative>(`cooperatives/${id}`);
      cooperativeName.value = data?.name ?? null;
    } catch {
      cooperativeName.value = null;
    }
  }

  async function login(credentials: LoginCredentials): Promise<void> {
    const response = await api.post<{ access_token: string; token_type: string }>('auth/login', credentials);

    token.value = response.data.access_token;
    localStorage.setItem('token', response.data.access_token);

    // Декодируем JWT токен для получения информации о пользователе
    const tokenParts = response.data.access_token.split('.');
    if (tokenParts.length < 2) {
      throw new Error('Invalid token format');
    }
    const payloadString = tokenParts[1];
    if (!payloadString) {
      throw new Error('Invalid token payload');
    }
    const payload = JSON.parse(atob(payloadString));
    user.value = {
      id: payload.sub,
      username: payload.username || payload.preferred_username || 'user',
      email: payload.email,
      role: payload.role || 'treasurer',
      cooperative_id: payload.cooperative_id,
      is_active: payload.is_active ?? true,
    };
    localStorage.setItem('user', JSON.stringify(user.value));

    await loadCooperativeName();
  }

  function logout(): void {
    token.value = null;
    user.value = null;
    cooperativeName.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) {
      return false;
    }

    try {
      // Проверяем валидность токена через health endpoint
      await api.get('/api/health');
      return true;
    } catch {
      logout();
      return false;
    }
  }

  return {
    token,
    user,
    cooperativeName,
    isAuthenticated,
    userRole,
    cooperativeId,
    login,
    logout,
    checkAuth,
    loadCooperativeName,
  };
});
