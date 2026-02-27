<template>
  <div class="cash-flow-report-view">
    <header class="view-header">
      <h1>Отчёт о движении средств</h1>
    </header>

    <div class="filter-bar">
      <div class="date-range">
        <div class="form-group">
          <label for="period_start">Начало периода:</label>
          <input
            id="period_start"
            v-model="periodStart"
            type="date"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="period_end">Конец периода:</label>
          <input
            id="period_end"
            v-model="periodEnd"
            type="date"
            class="form-input"
          />
        </div>
      </div>
      <button
        class="btn btn-primary"
        :disabled="loading || !canGenerate"
        @click="generateReport"
      >
        {{ loading ? 'Загрузка...' : 'Сформировать отчёт' }}
      </button>
    </div>

    <p v-if="error" class="error-message">{{ error }}</p>

    <div v-if="loading" class="loading">Загрузка отчёта…</div>

    <div v-else-if="report" class="report-content">
      <div class="report-period">
        <strong>Период:</strong>
        {{ formatDate(report.period_start) }} — {{ formatDate(report.period_end) }}
      </div>

      <div class="report-grid">
        <div class="report-item positive">
          <span class="label">Всего начислений:</span>
          <span class="value">{{ formatCurrency(report.total_accruals) }}</span>
        </div>
        <div class="report-item negative">
          <span class="label">Всего платежей:</span>
          <span class="value">{{ formatCurrency(report.total_payments) }}</span>
        </div>
        <div class="report-item negative">
          <span class="label">Всего расходов:</span>
          <span class="value">{{ formatCurrency(report.total_expenses) }}</span>
        </div>
        <div class="report-item total" :class="{ 'positive-balance': report.net_balance >= 0, 'negative-balance': report.net_balance < 0 }">
          <span class="label">Чистый баланс:</span>
          <span class="value">{{ formatCurrency(report.net_balance) }}</span>
        </div>
      </div>

      <div class="report-actions">
        <button class="btn btn-secondary" @click="exportToCSV">
          Экспорт в CSV
        </button>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>Выберите период и нажмите «Сформировать отчёт»</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useReportsStore } from '@/stores/reports';
import type { CashFlowReport } from '@/types';

const authStore = useAuthStore();
const reportsStore = useReportsStore();

const periodStart = ref<string>('');
const periodEnd = ref<string>('');
const report = ref<CashFlowReport | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const canGenerate = computed(() => periodStart.value && periodEnd.value);

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function formatCurrency(amount: number): string {
  return amount.toLocaleString('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + ' BYN';
}

async function generateReport(): Promise<void> {
  if (!canGenerate.value) return;

  loading.value = true;
  error.value = null;
  report.value = null;

  try {
    const coopId = authStore.cooperativeId;
    if (!coopId) {
      throw new Error('Не определено СТ пользователя');
    }

    await reportsStore.fetchCashFlowReport(coopId, periodStart.value, periodEnd.value);
    report.value = reportsStore.cashFlowReport;
  } catch (e: unknown) {
    const message = e && typeof e === 'object' && 'response' in e
      ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
      : 'Не удалось сформировать отчёт';
    error.value = typeof message === 'string' ? message : 'Ошибка формирования отчёта';
  } finally {
    loading.value = false;
  }
}

function exportToCSV(): void {
  if (!report.value) return;

  const headers = ['Показатель', 'Значение'];
  const rows = [
    ['Период', `${report.value.period_start} — ${report.value.period_end}`],
    ['Всего начислений', report.value.total_accruals.toString()],
    ['Всего платежей', report.value.total_payments.toString()],
    ['Всего расходов', report.value.total_expenses.toString()],
    ['Чистый баланс', report.value.net_balance.toString()],
  ];

  const csvContent = [
    headers.join(';'),
    ...rows.map(row => row.join(';'))
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `cash-flow-report-${report.value.period_start}-${report.value.period_end}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

onMounted(() => {
  // Установить период по умолчанию — текущий месяц
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

  periodStart.value = String(firstDay.toISOString().split('T')[0]);
  periodEnd.value = String(lastDay.toISOString().split('T')[0]);
});
</script>

<style scoped>
.cash-flow-report-view {
  padding: 1.5rem;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.view-header {
  margin-bottom: 1.25rem;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.date-range {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.report-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.report-period {
  margin-bottom: 1.25rem;
  padding: 0.75rem 1rem;
  background: var(--color-primary-light);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--color-primary);
  font-size: var(--text-sm);
}

.report-grid {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.report-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: var(--color-bg);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--color-border);
}

.report-item.positive {
  border-left-color: var(--color-success);
  background: #f0fdf4;
}

.report-item.negative {
  border-left-color: var(--color-error);
  background: var(--color-error-bg);
}

.report-item.total {
  border-left-color: var(--color-primary);
  background: var(--color-primary-light);
  font-weight: var(--font-semibold);
}

.report-item.total.positive-balance {
  border-left-color: var(--color-success);
  background: #f0fdf4;
}

.report-item.total.negative-balance {
  border-left-color: var(--color-error);
  background: var(--color-error-bg);
}

.report-item .label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.report-item .value {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.report-actions {
  display: flex;
  gap: 0.75rem;
}
</style>
