<template>
  <div class="payments-container">
    <div class="page-header">
      <h1>Платежи</h1>
      <router-link to="/payments/create" class="create-button">
        <Plus class="create-button-icon" aria-hidden />
        Зарегистрировать платёж
      </router-link>
    </div>

    <!-- Фильтры -->
    <div class="filters-card">
      <div class="filters-row">
        <div class="filter-group">
          <label for="status-filter">Статус</label>
          <select id="status-filter" v-model="statusFilter">
            <option value="">Все</option>
            <option value="confirmed">Подтверждённые</option>
            <option value="cancelled">Отменённые</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="date-from">Дата с</label>
          <input id="date-from" v-model="dateFrom" type="date" />
        </div>

        <div class="filter-group">
          <label for="date-to">Дата по</label>
          <input id="date-to" v-model="dateTo" type="date" />
        </div>

        <button class="filter-button" @click="fetchData">Применить</button>
      </div>
    </div>

    <!-- Список платежей -->
    <div class="payments-card">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка платежей...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button class="retry-button" @click="fetchData">Попробовать снова</button>
      </div>

      <div v-else-if="payments.length === 0" class="empty-state">
        <p>Платежи не найдены</p>
        <router-link to="/payments/create" class="create-link">Зарегистрировать первый платёж</router-link>
      </div>

      <div v-else class="payments-table-wrapper">
        <table class="payments-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Фин. субъект</th>
              <th>Плательщик</th>
              <th>Сумма</th>
              <th>Дата</th>
              <th>Документ</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="payment in filteredPayments" :key="payment.id" class="payment-row">
              <td class="id-cell">
                <code>{{ shortId(payment.id) }}</code>
              </td>
              <td>
                <div class="fs-info">
                  <span class="fs-code">{{ getFsCode(payment.financial_subject_id) }}</span>
                </div>
              </td>
              <td>
                <span class="payer-name">{{ getPayerName(payment.payer_owner_id) }}</span>
              </td>
              <td class="amount-cell">
                <span :class="['amount-value', payment.status === 'cancelled' ? 'cancelled' : '']">
                  {{ formatAmount(payment.amount) }} BYN
                </span>
              </td>
              <td>{{ formatDate(payment.payment_date) }}</td>
              <td>
                <span v-if="payment.document_number" class="document-number">
                  {{ payment.document_number }}
                </span>
                <span v-else class="no-document">—</span>
              </td>
              <td>
                <span :class="['status-badge', payment.status]">
                  {{ payment.status === 'confirmed' ? 'Подтверждён' : 'Отменён' }}
                </span>
              </td>
              <td>
                <button
                  v-if="payment.status === 'confirmed'"
                  class="cancel-button"
                  :disabled="isCancelling"
                  @click="cancelPayment(payment.id)"
                >
                  Отменить
                </button>
                <span v-else class="no-action">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Plus } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { usePaymentsStore } from '@/stores/payments';
import type { Payment, FinancialSubject, Owner } from '@/types';

const authStore = useAuthStore();
const paymentsStore = usePaymentsStore();

const payments = ref<Payment[]>([]);
const financialSubjectsMap = ref<Map<string, FinancialSubject>>(new Map());
const ownersMap = ref<Map<string, Owner>>(new Map());
const loading = ref(false);
const error = ref<string | null>(null);
const isCancelling = ref(false);

// Фильтры
const statusFilter = ref('');
const dateFrom = ref('');
const dateTo = ref('');

const currentCooperativeId = computed(() => authStore.cooperativeId);
const isAdmin = computed(() => authStore.userRole === 'admin');

const filteredPayments = computed(() => {
  let result = [...payments.value];

  if (statusFilter.value) {
    result = result.filter((p) => p.status === statusFilter.value);
  }

  if (dateFrom.value) {
    result = result.filter((p) => p.payment_date >= dateFrom.value);
  }

  if (dateTo.value) {
    result = result.filter((p) => p.payment_date <= dateTo.value);
  }

  return result.sort((a, b) => new Date(b.payment_date).getTime() - new Date(a.payment_date).getTime());
});

onMounted(async () => {
  await fetchData();
});

async function fetchData(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    const coopId = isAdmin.value ? null : currentCooperativeId.value;
    await paymentsStore.fetchPayments(coopId);
    payments.value = paymentsStore.payments;

    // Загружаем фин. субъекты и владельцев для отображения
    await paymentsStore.fetchFinancialSubjects(coopId || '');
    await paymentsStore.fetchOwners(coopId || '');

    // Создаём мапы для быстрого поиска
    financialSubjectsMap.value = new Map(
      paymentsStore.financialSubjects.map((fs) => [fs.id, fs])
    );
    ownersMap.value = new Map(paymentsStore.owners.map((o) => [o.id, o]));
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка загрузки';
  } finally {
    loading.value = false;
  }
}

function shortId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}...` : id;
}

function getFsCode(fsId: string): string {
  const fs = financialSubjectsMap.value.get(fsId);
  return fs ? fs.code : 'Неизвестно';
}

function getPayerName(ownerId: string): string {
  const owner = ownersMap.value.get(ownerId);
  return owner ? owner.name : 'Неизвестно';
}

function formatAmount(amount: number): string {
  return amount.toFixed(2).replace('.', ',');
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

async function cancelPayment(paymentId: string): Promise<void> {
  if (!confirm('Вы уверены, что хотите отменить этот платёж?')) {
    return;
  }
  isCancelling.value = true;
  try {
    await paymentsStore.cancelPayment(paymentId);
    await fetchData();
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Ошибка при отмене платежа');
  } finally {
    isCancelling.value = false;
  }
}
</script>

<style scoped>
.payments-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.create-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: linear-gradient(180deg, #14b8a6 0%, var(--color-primary) 100%);
  color: white;
  text-decoration: none;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  transition: background var(--transition-base), box-shadow var(--transition-base);
}

.create-button:hover {
  background: linear-gradient(180deg, #0d9488 0%, var(--color-primary-hover) 100%);
  box-shadow: var(--shadow-md);
}

.create-button-icon {
  width: 1.125rem;
  height: 1.125rem;
}

.filters-card {
  background: var(--color-bg-card);
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  margin-bottom: 1.5rem;
}

.filters-row {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.filter-group label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
}

.filter-group select,
.filter-group input {
  padding: 0.5rem 0.875rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  background: var(--color-bg-card);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.filter-group select:focus,
.filter-group input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.filter-button {
  padding: 0.5rem 1.25rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: background 0.2s;
  align-self: flex-end;
}

.filter-button:hover {
  background: var(--color-primary-hover);
}

.payments-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.loading-state,
.error-state,
.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
}

.loading-state p,
.error-state p,
.empty-state p {
  margin: 1rem 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.spinner {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-button,
.create-link {
  display: inline-flex;
  align-items: center;
  padding: 0.625rem 1.25rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s;
}

.retry-button:hover,
.create-link:hover {
  background: var(--color-primary-hover);
}

.payments-table-wrapper {
  overflow-x: auto;
}

.payments-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.payments-table th {
  padding: 0.875rem 1.25rem;
  background: var(--color-bg-elevated);
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.payments-table td {
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid var(--color-border);
}

.payment-row:hover {
  background: var(--color-primary-subtle);
}

.id-cell code {
  font-family: ui-monospace, monospace;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.fs-code {
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.amount-value {
  color: var(--color-success);
  font-weight: var(--font-semibold);
}

.amount-value.cancelled {
  color: var(--color-text-muted);
  text-decoration: line-through;
}

.document-number {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.status-badge.confirmed {
  background: var(--color-primary-light);
  color: var(--color-primary-hover);
}

.status-badge.cancelled {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.cancel-button {
  padding: 0.375rem 0.75rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-error);
  color: var(--color-error);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.cancel-button:hover:not(:disabled) {
  background: var(--color-error);
  color: white;
}

.cancel-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
