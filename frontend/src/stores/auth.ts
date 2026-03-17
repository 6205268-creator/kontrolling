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
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    const response = await api.post<{ access_token?: string; token_type?: string }>(
      'auth/login',
      formData,
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        timeout: 15000,
      }
    );

    const accessToken = response.data?.access_token;
    if (typeof accessToken !== 'string' || !accessToken) {
      throw new Error('Сервер вернул неверный ответ: нет токена. Проверьте, что бэкенд запущен и доступен.');
    }

    token.value = accessToken;
    localStorage.setItem('token', accessToken);

    // Декодируем JWT токен для получения информации о пользователе
    const tokenParts = accessToken.split('.');
    if (tokenParts.length < 2) {
      throw new Error('Неверный формат токена от сервера.');
    }
    const payloadString = tokenParts[1];
    if (!payloadString) {
      throw new Error('Неверные данные токена.');
    }
    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(atob(payloadString));
    } catch {
      throw new Error('Не удалось прочитать данные пользователя из токена.');
    }
    const coopId = payload.cooperative_id;
    user.value = {
      id: String(payload.sub ?? ''),
      username: (payload.username as string) || (payload.preferred_username as string) || credentials.username,
      email: typeof payload.email === 'string' ? payload.email : '',
      role: (payload.role as User['role']) || 'treasurer',
      cooperative_id: coopId != null && coopId !== '' ? String(coopId) : null,
      is_active: (payload.is_active as boolean) ?? true,
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

  return {
    token,
    user,
    cooperativeName,
    isAuthenticated,
    userRole,
    cooperativeId,
    login,
    logout,
    loadCooperativeName,
  };
});
