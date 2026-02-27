<template>
  <div class="form-view">
    <h1>Создание начисления</h1>
    <form class="form" @submit.prevent="onSubmit">
      <section class="form-section">
        <h2>Данные начисления</h2>
        <div v-if="isAdmin" class="field">
          <label for="cooperative">Садовое товарищество (СТ) *</label>
          <select
            id="cooperative"
            v-model="selectedCooperativeId"
            required
            @change="onCooperativeChange"
          >
            <option value="">— Выберите СТ —</option>
            <option v-for="c in cooperatives" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </select>
        </div>
        <div v-else class="field">
          <label>Садовое товарищество</label>
          <p class="readonly-value">{{ currentCooperativeName }}</p>
        </div>
        <div class="field">
          <label for="financial_subject">Финансовый субъект *</label>
          <select
            id="financial_subject"
            v-model="form.financial_subject_id"
            required
            :disabled="!fsList.length"
          >
            <option value="">— Выберите ФС —</option>
            <option v-for="fs in fsList" :key="fs.id" :value="fs.id">
              {{ fs.code }} ({{ subjectTypeLabel(fs.subject_type) }})
            </option>
          </select>
          <p v-if="fsCooperativeId && !fsList.length" class="hint">Загрузите список ФС, выбрав СТ</p>
        </div>
        <div class="field">
          <label for="contribution_type">Тип взноса *</label>
          <select id="contribution_type" v-model="form.contribution_type_id" required>
            <option value="">— Выберите тип взноса —</option>
            <option v-for="ct in contributionTypes" :key="ct.id" :value="ct.id">
              {{ ct.name }} ({{ ct.code }})
            </option>
          </select>
        </div>
        <div class="field">
          <label for="amount">Сумма (BYN) *</label>
          <input
            id="amount"
            v-model.number="form.amount"
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            required
          />
        </div>
        <div class="field">
          <label for="accrual_date">Дата начисления *</label>
          <input id="accrual_date" v-model="form.accrual_date" type="date" required />
        </div>
        <div class="field">
          <label for="period_start">Начало периода *</label>
          <input id="period_start" v-model="form.period_start" type="date" required />
        </div>
        <div class="field">
          <label for="period_end">Конец периода</label>
          <input id="period_end" v-model="form.period_end" type="date" />
        </div>
      </section>

      <div v-if="validationError" class="validation-error">{{ validationError }}</div>
      <div v-if="submitError" class="validation-error">{{ submitError }}</div>

      <div class="form-actions">
        <router-link to="/accruals" class="btn-secondary">Отмена</router-link>
        <button type="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? 'Создание…' : 'Создать начисление' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { useAuthStore } from '@/stores/auth';
import { useAccrualsStore } from '@/stores/accruals';
import type { Cooperative, ContributionType } from '@/types';

interface FinancialSubjectInfo {
  id: string;
  subject_type: string;
  subject_id: string;
  cooperative_id: string;
  code: string;
  status: string;
}

const router = useRouter();
const authStore = useAuthStore();
const accrualsStore = useAccrualsStore();

const cooperatives = ref<Cooperative[]>([]);
const fsList = ref<FinancialSubjectInfo[]>([]);
const contributionTypes = ref<ContributionType[]>([]);

const form = ref({
  financial_subject_id: '',
  contribution_type_id: '',
  amount: null as number | null,
  accrual_date: '',
  period_start: '',
  period_end: '' as string,
});

const validationError = ref('');
const submitError = ref('');
const submitting = ref(false);

const isAdmin = computed(() => authStore.userRole === 'admin');
const fsCooperativeId = computed(() => {
  if (isAdmin.value) return selectedCooperativeId.value;
  return authStore.cooperativeId ?? '';
});
const selectedCooperativeId = ref('');

const currentCooperativeName = computed(() => {
  const id = isAdmin.value ? selectedCooperativeId.value : authStore.cooperativeId ?? '';
  if (!id) return '—';
  const c = cooperatives.value.find((x) => x.id === id);
  return c?.name ?? id;
});

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function subjectTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    LAND_PLOT: 'Участок',
    WATER_METER: 'Вода',
    ELECTRICITY_METER: 'Электричество',
    GENERAL_DECISION: 'Общее решение',
  };
  return labels[type] ?? type;
}

async function loadFinancialSubjects(): Promise<void> {
  const coopId = fsCooperativeId.value;
  if (!coopId) {
    fsList.value = [];
    return;
  }
  try {
    const { data } = await api.get<FinancialSubjectInfo[]>('financial-subjects/', {
      params: { cooperative_id: coopId },
    });
    fsList.value = data ?? [];
    if (form.value.financial_subject_id && !fsList.value.some((fs) => fs.id === form.value.financial_subject_id)) {
      form.value.financial_subject_id = '';
    }
  } catch {
    fsList.value = [];
  }
}

function onCooperativeChange(): void {
  form.value.financial_subject_id = '';
  loadFinancialSubjects();
}

watch(fsCooperativeId, (id) => {
  if (id) loadFinancialSubjects();
});

function validate(): boolean {
  validationError.value = '';
  if (!form.value.financial_subject_id) {
    validationError.value = 'Выберите финансовый субъект.';
    return false;
  }
  if (!form.value.contribution_type_id) {
    validationError.value = 'Выберите тип взноса.';
    return false;
  }
  const amount = form.value.amount;
  if (amount == null || amount < 0) {
    validationError.value = 'Укажите сумму не меньше 0.';
    return false;
  }
  if (!form.value.accrual_date) {
    validationError.value = 'Укажите дату начисления.';
    return false;
  }
  if (!form.value.period_start) {
    validationError.value = 'Укажите начало периода.';
    return false;
  }
  return true;
}

async function onSubmit(): Promise<void> {
  submitError.value = '';
  if (!validate()) return;
  const payload = {
    financial_subject_id: form.value.financial_subject_id,
    contribution_type_id: form.value.contribution_type_id,
    amount: Number(form.value.amount),
    accrual_date: form.value.accrual_date,
    period_start: form.value.period_start,
    period_end: form.value.period_end || undefined,
  };
  submitting.value = true;
  try {
    await accrualsStore.createAccrual(payload);
    await router.push('/accruals');
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null;
    submitError.value = typeof msg === 'string' ? msg : 'Не удалось создать начисление. Попробуйте снова.';
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  if (isAdmin.value) {
    try {
      const { data } = await api.get<Cooperative[]>('cooperatives/');
      cooperatives.value = data ?? [];
    } catch {
      cooperatives.value = [];
    }
  } else {
    try {
      const { data } = await api.get<Cooperative[]>('cooperatives/');
      cooperatives.value = data ?? [];
    } catch {
      cooperatives.value = [];
    }
    selectedCooperativeId.value = authStore.cooperativeId ?? '';
  }
  try {
    const { data } = await api.get<ContributionType[]>('contribution-types/');
    contributionTypes.value = data ?? [];
  } catch {
    contributionTypes.value = [];
  }
  const defaultDate = todayISO();
  if (!form.value.accrual_date) form.value.accrual_date = defaultDate;
  if (!form.value.period_start) form.value.period_start = defaultDate;
  await loadFinancialSubjects();
});
</script>

<style scoped>
.form-view {
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  max-width: 720px;
}

.form-view h1 {
  margin: 0 0 24px;
  font-size: 1.5rem;
}

.form-section {
  margin-bottom: 28px;
}

.form-section h2 {
  margin: 0 0 16px;
  font-size: 1.1rem;
  color: #374151;
}

.field {
  margin-bottom: 14px;
}

.field label {
  display: block;
  margin-bottom: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.field input,
.field select {
  width: 100%;
  max-width: 320px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.field select:disabled {
  background: #f3f4f6;
  color: #6b7280;
}

.readonly-value {
  margin: 0;
  padding: 8px 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.hint {
  margin: 4px 0 0;
  font-size: 0.75rem;
  color: #6b7280;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.btn-secondary {
  padding: 10px 18px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  font-size: 0.875rem;
  cursor: pointer;
  text-decoration: none;
  color: #374151;
  display: inline-block;
}

.btn-secondary:hover {
  background: #f9fafb;
}

.btn-primary {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.95;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.validation-error {
  margin-top: 12px;
  padding: 10px 12px;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 6px;
  font-size: 0.875rem;
}
</style>
