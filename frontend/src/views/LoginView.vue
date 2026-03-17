<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-logo">
        <LayoutDashboard class="logo-icon" aria-hidden />
      </div>
      <h1 class="login-title">Контроллинг-СТ</h1>
      <p class="login-subtitle">Вход в систему</p>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Имя пользователя</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Введите имя пользователя"
            required
            :disabled="isLoading"
            @input="clearError"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <div class="password-wrapper">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Введите пароль"
              required
              :disabled="isLoading"
              @input="clearError"
              @keydown.enter.prevent="handleLogin"
            />
            <button
              type="button"
              class="password-toggle"
              :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
              :title="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'Скрыть' : 'Показать' }}
            </button>
          </div>
        </div>

        <div class="login-error-box" role="alert">
          {{ inlineError }}
          <template v-if="inlineError && inlineError.includes('Сервер')">
            <p class="login-error-hint">
              Проверка: откройте в браузере
              <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener">http://127.0.0.1:8000/docs</a>
              — если страница не открывается, бэкенд не запущен на порту 8000.
            </p>
            <button type="button" class="btn-check-server" @click="checkServer">
              {{ checkStatus ?? 'Проверить связь с сервером' }}
            </button>
          </template>
        </div>
        <button
          type="button"
          class="login-button"
          :disabled="isLoading"
          @click="handleLogin"
        >
          <LogIn v-if="!isLoading" class="btn-icon" aria-hidden />
          <span v-if="isLoading">Вход...</span>
          <span v-else>Войти</span>
        </button>
      </form>
    </div>
    <div class="build-label">Сборка: {{ buildTimestamp }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { LayoutDashboard, LogIn } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { error as errorToast, success as successToast } from '@/utils/toast';
import api from '@/services/api';

const router = useRouter();
const authStore = useAuthStore();

const buildTimestamp = typeof __BUILD_TIMESTAMP__ !== 'undefined' ? __BUILD_TIMESTAMP__ : '—';

const username = ref('');
const password = ref('');
const showPassword = ref(false);
const isLoading = ref(false);
const inlineError = ref('');
const checkStatus = ref<string | null>(null);

function clearError() {
  inlineError.value = '';
  checkStatus.value = null;
}

async function checkServer() {
  checkStatus.value = 'Проверка…';
  try {
    const { data } = await api.get<{ status?: string }>('health');
    if (data?.status === 'ok') {
      checkStatus.value = 'Сервер доступен (health ok)';
    } else {
      checkStatus.value = `Ответ: ${JSON.stringify(data)}`;
    }
  } catch (e: unknown) {
    const msg = e && typeof e === 'object' && 'message' in e ? (e as Error).message : String(e);
    const code = e && typeof e === 'object' && 'code' in e ? (e as { code: string }).code : '';
    checkStatus.value = `Ошибка: ${code || msg}`;
  }
}

async function handleLogin() {
  inlineError.value = '';
  isLoading.value = true;

  try {
    await authStore.login({
      username: username.value,
      password: password.value,
    });

    try {
      successToast('Добро пожаловать!', `Вы вошли как ${username.value}`);
    } catch {
      // toast может быть недоступен — не мешаем переходу
    }
    await router.push('/dashboard');
  } catch (err: unknown) {
    let errorMessage = 'Произошла ошибка при входе';

    if (err && typeof err === 'object' && 'response' in err) {
      const axiosError = err as {
        response?: { status?: number; data?: { detail?: unknown; message?: string } };
        message?: string;
      };

      if (axiosError.response?.status === 401) {
        errorMessage = 'Неверное имя пользователя или пароль';
      } else if (axiosError.response?.status === 502 || axiosError.response?.status === 503) {
        errorMessage = 'Сервер недоступен. Проверьте, что бэкенд запущен на порту 8000.';
      } else if (axiosError.response?.status === 500) {
        const data = axiosError.response?.data;
        const detail = data && typeof data === 'object' && 'detail' in data ? (data as { detail: unknown }).detail : undefined;
        errorMessage = typeof detail === 'string' ? detail : 'Ошибка сервера. Проверьте подключение к БД.';
      } else if (axiosError.response?.data?.message) {
        errorMessage = axiosError.response.data.message;
      } else if (axiosError.response?.status === 404 || axiosError.response?.status === 0) {
        errorMessage = 'Не удалось подключиться к серверу. Запустите бэкенд (npm run dev из корня проекта).';
      } else if (axiosError.message) {
        errorMessage = axiosError.message;
      }
    } else if (err instanceof Error) {
      if ('code' in err && (err as { code: string }).code === 'ECONNABORTED') {
        errorMessage = 'Сервер не отвечает. Запустите бэкенд (npm run dev из корня проекта).';
      } else {
        errorMessage = err.message;
      }
    }

    inlineError.value = errorMessage;
    try {
      errorToast('Ошибка входа', errorMessage);
    } catch {
      // тост может не сработать — текст уже в inlineError
    }
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(165deg, var(--color-sidebar) 0%, var(--color-sidebar-active) 45%, var(--color-primary-hover) 100%);
  padding: 1.5rem;
}

.login-card {
  background: var(--color-bg-card);
  padding: 2.5rem;
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-xl);
  width: 100%;
  max-width: 420px;
}

.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.logo-icon {
  width: 48px;
  height: 48px;
  color: var(--color-primary);
}

.login-title {
  margin: 0 0 0.25rem 0;
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  text-align: center;
  letter-spacing: -0.03em;
}

.login-subtitle {
  margin: 0 0 1.75rem 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.login-form .form-group label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.login-form .form-group input {
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.login-form .form-group input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.password-wrapper {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.password-wrapper input {
  flex: 1;
}

.password-toggle {
  flex-shrink: 0;
  padding: 0.5rem 0.75rem;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-primary);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  white-space: nowrap;
  transition: border-color var(--transition-base), background var(--transition-base);
}

.password-toggle:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-subtle);
}

.login-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.25rem;
  background: linear-gradient(135deg, var(--color-primary-gradient-from) 0%, var(--color-primary-gradient-to) 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: background var(--transition-base), box-shadow var(--transition-base);
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.login-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, var(--color-primary-hover) 100%);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.25);
  transform: translateY(-1px);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-error-box {
  min-height: 0;
  margin: 0;
  padding: 0.75rem 1rem;
  font-size: var(--text-sm);
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  visibility: visible;
}

.login-error-box:empty {
  display: none;
}

.login-error-box:not(:empty) {
  margin-bottom: 0.25rem;
}

.login-error-hint {
  margin: 0.5rem 0 0;
  font-size: 0.8125rem;
  color: #991b1b;
}

.login-error-hint a {
  color: #b91c1c;
  text-decoration: underline;
}

.btn-check-server {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  background: #fff;
  border: 1px solid #f87171;
  border-radius: var(--radius-md);
  color: #b91c1c;
  cursor: pointer;
}

.btn-check-server:hover {
  background: #fef2f2;
}

.btn-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.build-label {
  position: fixed;
  bottom: 0.75rem;
  right: 1rem;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  opacity: 0.6;
  pointer-events: none;
}
</style>
