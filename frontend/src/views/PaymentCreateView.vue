<template>
  <div class="payment-create-container">
    <div class="page-header">
      <h1>Регистрация платежа</h1>
      <router-link to="/payments" class="back-button">← Назад к списку</router-link>
    </div>

    <div class="form-card">
      <form class="payment-form" @submit.prevent="handleSubmit">
        <!-- Финансовый субъект -->
        <div class="form-group">
          <label for="financial-subject">Финансовый субъект *</label>
          <div class="autocomplete">
            <input
              id="financial-subject"
              ref="fsInput"
              v-model="fsSearchQuery"
              type="text"
              placeholder="Начните вводить код или название"
              required
              :disabled="isLoading"
              @focus="onFsFocus"
              @input="onFsInput"
              @blur="hideFsSuggestions"
            />
            <ul v-if="showFsSuggestions && fsSuggestions.length > 0" class="suggestions-list">
              <li
                v-for="fs in fsSuggestions"
                :key="fs.id"
                class="suggestion-item"
                @mousedown.prevent="selectFs(fs)"
              >
                <span class="fs-code">{{ fs.code }}</span>
                <span class="fs-details">{{ getFsDetails(fs) }}</span>
              </li>
            </ul>
          </div>
          <input v-model="form.financial_subject_id" type="hidden" />
          <p v-if="selectedFs" class="selected-value">
            Выбрано: <strong>{{ selectedFs.code }}</strong>
          </p>
        </div>

        <!-- Плательщик -->
        <div class="form-group">
          <label for="payer">Плательщик *</label>
          <div class="autocomplete">
            <input
              id="payer"
              ref="payerInput"
              v-model="payerSearchQuery"
              type="text"
              placeholder="Начните вводить имя или УНП"
              required
              :disabled="isLoading"
              @focus="onPayerFocus"
              @input="onPayerInput"
              @blur="hidePayerSuggestions"
            />
            <ul v-if="showPayerSuggestions && payerSuggestions.length > 0" class="suggestions-list">
              <li
                v-for="owner in payerSuggestions"
                :key="owner.id"
                class="suggestion-item"
                @mousedown.prevent="selectPayer(owner)"
              >
                <span class="owner-name">{{ owner.name }}</span>
                <span v-if="owner.tax_id" class="owner-tax">УНП: {{ owner.tax_id }}</span>
              </li>
            </ul>
          </div>
          <input v-model="form.payer_owner_id" type="hidden" />
          <p v-if="selectedPayer" class="selected-value">
            Выбрано: <strong>{{ selectedPayer.name }}</strong>
          </p>
        </div>

        <!-- Сумма -->
        <div class="form-group">
          <label for="amount">Сумма (BYN) *</label>
          <input
            id="amount"
            v-model.number="form.amount"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0.00"
            required
            :disabled="isLoading"
          />
        </div>

        <!-- Дата платежа -->
        <div class="form-group">
          <label for="payment-date">Дата платежа *</label>
          <input
            id="payment-date"
            v-model="form.payment_date"
            type="date"
            required
            :disabled="isLoading"
          />
        </div>

        <!-- Номер документа -->
        <div class="form-group">
          <label for="document-number">Номер документа</label>
          <input
            id="document-number"
            v-model="form.document_number"
            type="text"
            placeholder="Например: П-001"
            :disabled="isLoading"
          />
        </div>

        <!-- Описание -->
        <div class="form-group">
          <label for="description">Описание</label>
          <textarea
            id="description"
            v-model="form.description"
            rows="3"
            placeholder="Назначение платежа"
            :disabled="isLoading"
          ></textarea>
        </div>

        <!-- Ошибка -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Кнопки -->
        <div class="form-actions">
          <button type="submit" class="submit-button" :disabled="isLoading || !canSubmit">
            <span v-if="isLoading">Регистрация...</span>
            <span v-else>Зарегистрировать платёж</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { usePaymentsStore } from '@/stores/payments';
import type { FinancialSubject, Owner } from '@/types';

const router = useRouter();
const authStore = useAuthStore();
const paymentsStore = usePaymentsStore();

const form = ref({
  financial_subject_id: '',
  payer_owner_id: '',
  amount: 0,
  payment_date: new Date().toISOString().split('T')[0],
  document_number: '',
  description: '',
});

const isLoading = ref(false);
const error = ref('');

// Финансовый субъект
const fsSearchQuery = ref('');
const selectedFs = ref<FinancialSubject | null>(null);
const fsSuggestions = ref<FinancialSubject[]>([]);
const showFsSuggestions = ref(false);
const fsInputTimeout = ref<ReturnType<typeof setTimeout> | null>(null);

// Плательщик
const payerSearchQuery = ref('');
const selectedPayer = ref<Owner | null>(null);
const payerSuggestions = ref<Owner[]>([]);
const showPayerSuggestions = ref(false);
const payerInputTimeout = ref<ReturnType<typeof setTimeout> | null>(null);

const currentCooperativeId = computed(() => authStore.cooperativeId);
const isAdmin = computed(() => authStore.userRole === 'admin');

const canSubmit = computed(() => {
  return (
    form.value.financial_subject_id !== '' &&
    form.value.payer_owner_id !== '' &&
    form.value.amount > 0 &&
    form.value.payment_date !== ''
  );
});

onMounted(async () => {
  const coopId = isAdmin.value ? null : currentCooperativeId.value;
  await paymentsStore.fetchFinancialSubjects(coopId || '');
  await paymentsStore.fetchOwners(coopId || '');
});

// Финансовый субъект - автокомплит
function onFsInput(): void {
  selectedFs.value = null;
  form.value.financial_subject_id = '';
  fsSuggestions.value = [];
  if (fsInputTimeout.value) clearTimeout(fsInputTimeout.value);
  if (fsSearchQuery.value.trim().length < 1) {
    showFsSuggestions.value = false;
    return;
  }
  fsInputTimeout.value = setTimeout(async () => {
    const coopId = isAdmin.value ? null : currentCooperativeId.value;
    const results = await paymentsStore.searchFinancialSubjects(fsSearchQuery.value.trim(), coopId || '');
    fsSuggestions.value = results;
    showFsSuggestions.value = results.length > 0;
  }, 300);
}

function onFsFocus(): void {
  if (fsSuggestions.value.length > 0) {
    showFsSuggestions.value = true;
  }
}

function hideFsSuggestions(): void {
  setTimeout(() => {
    showFsSuggestions.value = false;
  }, 200);
}

function selectFs(fs: FinancialSubject): void {
  selectedFs.value = fs;
  form.value.financial_subject_id = fs.id;
  fsSearchQuery.value = fs.code;
  fsSuggestions.value = [];
  showFsSuggestions.value = false;
}

function getFsDetails(fs: FinancialSubject): string {
  const typeNames: Record<string, string> = {
    LAND_PLOT: 'Участок',
    WATER_METER: 'Вода',
    ELECTRICITY_METER: 'Электричество',
    GENERAL_DECISION: 'Общее решение',
  };
  const typeName = typeNames[fs.subject_type] || fs.subject_type;
  return `${typeName} • Статус: ${fs.status === 'active' ? 'Активен' : 'Закрыт'}`;
}

// Плательщик - автокомплит
function onPayerInput(): void {
  selectedPayer.value = null;
  form.value.payer_owner_id = '';
  payerSuggestions.value = [];
  if (payerInputTimeout.value) clearTimeout(payerInputTimeout.value);
  if (payerSearchQuery.value.trim().length < 2) {
    showPayerSuggestions.value = false;
    return;
  }
  payerInputTimeout.value = setTimeout(async () => {
    const results = await paymentsStore.searchOwners(payerSearchQuery.value.trim());
    payerSuggestions.value = results;
    showPayerSuggestions.value = results.length > 0;
  }, 300);
}

function onPayerFocus(): void {
  if (payerSuggestions.value.length > 0) {
    showPayerSuggestions.value = true;
  }
}

function hidePayerSuggestions(): void {
  setTimeout(() => {
    showPayerSuggestions.value = false;
  }, 200);
}

function selectPayer(owner: Owner): void {
  selectedPayer.value = owner;
  form.value.payer_owner_id = owner.id;
  payerSearchQuery.value = owner.name + (owner.tax_id ? ` (${owner.tax_id})` : '');
  payerSuggestions.value = [];
  showPayerSuggestions.value = false;
}

async function handleSubmit(): Promise<void> {
  error.value = '';
  if (!canSubmit.value) {
    error.value = 'Заполните все обязательные поля';
    return;
  }
  isLoading.value = true;
  try {
    await paymentsStore.registerPayment({
      financial_subject_id: form.value.financial_subject_id ?? '',
      payer_owner_id: form.value.payer_owner_id ?? '',
      amount: form.value.amount,
      payment_date: form.value.payment_date ?? '',
      document_number: form.value.document_number || undefined,
      description: form.value.description || undefined,
    });
    router.push('/payments');
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Ошибка при регистрации платежа';
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.payment-create-container {
  max-width: 700px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.back-button {
  padding: 8px 16px;
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.back-button:hover {
  color: #5568d3;
  text-decoration: underline;
}

.form-card {
  background: white;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.payment-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.form-group input,
.form-group textarea {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled,
.form-group textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.selected-value {
  font-size: 13px;
  color: #666;
  margin: 4px 0 0 0;
}

.autocomplete {
  position: relative;
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  max-height: 250px;
  overflow-y: auto;
  margin: 4px 0 0 0;
  padding: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  list-style: none;
}

.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: background 0.2s;
}

.suggestion-item:hover {
  background: #f5f7fa;
}

.fs-code {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.fs-details {
  font-size: 12px;
  color: #666;
}

.owner-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.owner-tax {
  font-size: 12px;
  color: #666;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.submit-button {
  flex: 1;
  padding: 14px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}
</style>
