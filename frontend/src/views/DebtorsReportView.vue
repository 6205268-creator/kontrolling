<template>
  <div class="debtors-report-view">
    <header class="view-header">
      <h1>Отчёт по должникам</h1>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-secondary"
          :disabled="sortedDebtors.length === 0"
          @click="exportCsv"
        >
          Экспорт в CSV
        </button>
      </div>
    </header>

    <div v-if="isAdmin" class="filter-bar cooperative-filter">
      <label for="cooperative-select">СТ:</label>
      <select
        id="cooperative-select"
        v-model="selectedCooperativeId"
        class="filter-select"
        @change="loadReport"
      >
        <option value="">— Выберите СТ —</option>
        <option
          v-for="c in cooperatives"
          :key="c.id"
          :value="c.id"
        >
          {{ c.name }}
        </option>
      </select>
    </div>

    <div v-if="!effectiveCooperativeId" class="message-box">
      <p>Выберите СТ для формирования отчёта.</p>
    </div>

    <template v-else>
      <div class="filter-bar">
        <label for="min-debt">Минимальная сумма долга (BYN):</label>
        <input
          id="min-debt"
          v-model.number="minDebtInput"
          type="number"
          min="0"
          step="0.01"
          class="filter-input"
        />
        <button type="button" class="btn btn-primary" @click="loadReport">
          Обновить
        </button>
      </div>

      <p v-if="reportsStore.error" class="error-message">
        {{ reportsStore.error }}
      </p>

      <div v-if="reportsStore.loading" class="loading">Загрузка…</div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Номер участка / счётчика</th>
              <th>Владелец</th>
              <th class="amount-col">Сумма долга (BYN)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="sortedDebtors.length === 0">
              <td colspan="3" class="empty">Нет должников с задолженностью выше указанного порога</td>
            </tr>
            <tr
              v-for="row in sortedDebtors"
              :key="row.financial_subject_id"
            >
              <td>{{ subjectDisplay(row) }}</td>
              <td>{{ row.owner_name }}</td>
              <td class="amount-col">{{ formatMoney(row.total_debt) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useReportsStore } from '@/stores/reports';
import type { DebtorInfo } from '@/types';
import type { Cooperative } from '@/types';
import api from '@/services/api';

const authStore = useAuthStore();
const reportsStore = useReportsStore();

const cooperatives = ref<Cooperative[]>([]);
const selectedCooperativeId = ref<string>('');
const minDebtInput = ref<number>(0);

const isAdmin = computed(() => authStore.userRole === 'admin');

const effectiveCooperativeId = computed(() => {
  if (isAdmin.value && selectedCooperativeId.value) {
    return selectedCooperativeId.value;
  }
  return authStore.cooperativeId ?? '';
});

const sortedDebtors = computed(() => {
  const list = [...reportsStore.debtorsReport];
  return list.sort((a, b) => b.total_debt - a.total_debt);
});

function subjectDisplay(row: DebtorInfo): string {
  const info = row.subject_info as Record<string, unknown>;
  if (row.subject_type === 'LAND_PLOT' && typeof info?.plot_number === 'string') {
    return `Участок № ${info.plot_number}`;
  }
  if (
    (row.subject_type === 'WATER_METER' || row.subject_type === 'ELECTRICITY_METER') &&
    info?.serial_number != null
  ) {
    return `Счётчик ${String(info.serial_number)}`;
  }
  return row.subject_type === 'LAND_PLOT' ? 'Участок' : 'Счётчик';
}

function formatMoney(value: number): string {
  return Number(value).toLocaleString('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function loadReport(): void {
  if (!effectiveCooperativeId.value) return;
  const minDebt = Number(minDebtInput.value);
  reportsStore.fetchDebtorsReport(effectiveCooperativeId.value, isNaN(minDebt) ? 0 : minDebt);
}

function exportCsv(): void {
  if (sortedDebtors.value.length === 0) return;
  const headers = ['Номер участка/счётчика', 'Владелец', 'Сумма долга (BYN)'];
  const rows = sortedDebtors.value.map((row) => [
    subjectDisplay(row),
    row.owner_name,
    formatMoney(row.total_debt),
  ]);
  const escape = (s: string) => {
    const t = String(s);
    return t.includes(',') || t.includes('"') || t.includes('\n') ? `"${t.replace(/"/g, '""')}"` : t;
  };
  const csv = [headers.map(escape).join(','), ...rows.map((r) => r.map(escape).join(','))].join('\r\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `debtors-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

onMounted(async () => {
  if (isAdmin.value) {
    try {
      const res = await api.get<Cooperative[]>('cooperatives/');
      cooperatives.value = res.data ?? [];
      const first = cooperatives.value[0];
      if (first && !selectedCooperativeId.value) {
        selectedCooperativeId.value = first.id;
      }
    } catch {
      cooperatives.value = [];
    }
  } else if (authStore.cooperativeId) {
    selectedCooperativeId.value = authStore.cooperativeId;
  }
  if (effectiveCooperativeId.value) {
    loadReport();
  }
});
</script>

<style scoped>
.debtors-report-view {
  padding: 1.5rem;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.filter-bar {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-bar label {
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.cooperative-filter {
  margin-bottom: 0.75rem;
}

.filter-input {
  padding: 0.5rem 0.875rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  width: 120px;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
}

.message-box {
  padding: 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.amount-col {
  text-align: right;
  white-space: nowrap;
}
</style>
