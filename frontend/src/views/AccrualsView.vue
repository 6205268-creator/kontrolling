<template>
  <div class="accruals-view list-view">
    <header class="view-header">
      <h1>Начисления</h1>
      <router-link
        v-if="canCreate"
        to="/accruals/create"
        class="btn btn-primary"
      >
        Создать начисление
      </router-link>
    </header>

    <div class="filter-bar">
      <template v-if="isAdmin">
        <label for="cooperative-filter">СТ:</label>
        <select
          id="cooperative-filter"
          v-model="selectedCooperativeId"
          class="filter-select"
          @change="loadAccruals"
        >
          <option value="">— Выберите СТ —</option>
          <option v-for="c in cooperatives" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </select>
      </template>
      <label v-if="fsList.length" for="fs-filter">Финансовый субъект:</label>
      <select
        v-if="fsList.length"
        id="fs-filter"
        v-model="selectedFsId"
        class="filter-select"
        @change="loadAccruals"
      >
        <option value="">Все</option>
        <option v-for="fs in fsList" :key="fs.id" :value="fs.id">
          {{ fs.code }}
        </option>
      </select>
    </div>

    <p v-if="accrualsStore.error" class="error-message">
      {{ accrualsStore.error }}
    </p>

    <div v-if="accrualsStore.loading" class="loading">Загрузка…</div>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>ФС</th>
            <th>Тип взноса</th>
            <th>Сумма</th>
            <th>Период</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="accrualsStore.accruals.length === 0">
            <td colspan="7" class="empty">Нет начислений</td>
          </tr>
          <tr v-for="a in accrualsStore.accruals" :key="a.id">
            <td>{{ formatDate(a.accrual_date) }}</td>
            <td>{{ fsCodeMap[a.financial_subject_id] ?? a.financial_subject_id }}</td>
            <td>{{ contributionTypeNameMap[a.contribution_type_id] ?? a.contribution_type_id }}</td>
            <td>{{ formatAmount(a.amount) }}</td>
            <td>{{ periodLabel(a) }}</td>
            <td>{{ statusLabel(a.status) }}</td>
            <td>
              <template v-if="a.status === 'created'">
                <button
                  type="button"
                  class="btn btn-apply"
                  :disabled="applyingId === a.id"
                  @click="apply(a.id)"
                >
                  {{ applyingId === a.id ? '…' : 'Применить' }}
                </button>
                <button
                  type="button"
                  class="btn btn-cancel"
                  :disabled="cancellingId === a.id"
                  @click="cancel(a.id)"
                >
                  {{ cancellingId === a.id ? '…' : 'Отменить' }}
                </button>
              </template>
              <span v-else class="no-action">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import api from '@/services/api';
import { useAuthStore } from '@/stores/auth';
import { useAccrualsStore } from '@/stores/accruals';
import type { Accrual, Cooperative, ContributionType } from '@/types';

interface FinancialSubjectInfo {
  id: string;
  code: string;
  cooperative_id: string;
}

const authStore = useAuthStore();
const accrualsStore = useAccrualsStore();

const cooperatives = ref<Cooperative[]>([]);
const fsList = ref<FinancialSubjectInfo[]>([]);
const contributionTypes = ref<ContributionType[]>([]);
const selectedCooperativeId = ref('');
const selectedFsId = ref('');
const applyingId = ref<string | null>(null);
const cancellingId = ref<string | null>(null);

const isAdmin = computed(() => authStore.userRole === 'admin');
const canCreate = computed(
  () => authStore.userRole === 'admin' || authStore.userRole === 'treasurer'
);

const fsCodeMap = computed(() => {
  const m: Record<string, string> = {};
  fsList.value.forEach((fs) => {
    m[fs.id] = fs.code;
  });
  return m;
});

const contributionTypeNameMap = computed(() => {
  const m: Record<string, string> = {};
  contributionTypes.value.forEach((ct) => {
    m[ct.id] = ct.name;
  });
  return m;
});

function formatDate(iso: string): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function formatAmount(amount: number): string {
  return Number(amount).toLocaleString('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function periodLabel(a: Accrual): string {
  const start = a.period_start ? formatDate(a.period_start) : '—';
  const end = a.period_end ? formatDate(a.period_end) : '';
  return end ? `${start} – ${end}` : start;
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    created: 'Создано',
    applied: 'Применено',
    cancelled: 'Отменено',
  };
  return labels[status] ?? status;
}

async function loadAccruals(): Promise<void> {
  const coopId = isAdmin.value ? selectedCooperativeId.value : (authStore.cooperativeId ?? '');
  if (!coopId) {
    accrualsStore.accruals = [];
    return;
  }
  await accrualsStore.fetchAccruals(
    selectedFsId.value ? { financial_subject_id: selectedFsId.value } : { cooperative_id: coopId }
  );
}

async function loadFsList(): Promise<void> {
  const coopId = isAdmin.value ? selectedCooperativeId.value : (authStore.cooperativeId ?? '');
  if (!coopId) {
    fsList.value = [];
    return;
  }
  try {
    const { data } = await api.get<FinancialSubjectInfo[]>('financial-subjects/', {
      params: { cooperative_id: coopId },
    });
    fsList.value = data ?? [];
    if (selectedFsId.value && !fsList.value.some((fs) => fs.id === selectedFsId.value)) {
      selectedFsId.value = '';
    }
  } catch {
    fsList.value = [];
  }
}

async function apply(id: string): Promise<void> {
  applyingId.value = id;
  try {
    await accrualsStore.applyAccrual(id);
    await loadAccruals();
  } finally {
    applyingId.value = null;
  }
}

async function cancel(id: string): Promise<void> {
  cancellingId.value = id;
  try {
    await accrualsStore.cancelAccrual(id);
    await loadAccruals();
  } finally {
    cancellingId.value = null;
  }
}

onMounted(async () => {
  if (isAdmin.value) {
    try {
      const { data } = await api.get<Cooperative[]>('cooperatives/');
      cooperatives.value = data ?? [];
      const first = cooperatives.value[0];
      if (first && !selectedCooperativeId.value) selectedCooperativeId.value = first.id;
    } catch {
      cooperatives.value = [];
    }
  } else {
    selectedCooperativeId.value = authStore.cooperativeId ?? '';
  }
  try {
    const { data } = await api.get<ContributionType[]>('contribution-types/');
    contributionTypes.value = data ?? [];
  } catch {
    contributionTypes.value = [];
  }
  await loadFsList();
  await loadAccruals();
});
</script>

<style scoped>
.accruals-view {
  padding: 1.5rem;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
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

.no-action {
  color: var(--color-text-muted);
}

.accruals-view .btn {
  margin-right: 0.5rem;
}
</style>
