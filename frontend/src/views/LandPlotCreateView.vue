<template>
  <div class="form-view">
    <h1>Создание участка</h1>
    <form class="form" @submit.prevent="onSubmit">
      <section class="form-section">
        <h2>Данные участка</h2>
        <div v-if="isAdmin" class="field">
          <label for="cooperative">Садовое товарищество (СТ) *</label>
          <select id="cooperative" v-model="form.cooperative_id" required>
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
          <label for="plot_number">Номер участка *</label>
          <input
            id="plot_number"
            v-model.trim="form.plot_number"
            type="text"
            maxlength="50"
            placeholder="Например: 42"
            required
          />
        </div>
        <div class="field">
          <label for="area_sqm">Площадь (кв. м) *</label>
          <input
            id="area_sqm"
            v-model.number="form.area_sqm"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="Например: 600"
            required
          />
        </div>
        <div class="field">
          <label for="cadastral_number">Кадастровый номер</label>
          <input
            id="cadastral_number"
            v-model.trim="form.cadastral_number"
            type="text"
            maxlength="50"
            placeholder="Необязательно"
          />
        </div>
        <div class="field">
          <label for="status">Статус</label>
          <select id="status" v-model="form.status">
            <option value="active">Активный</option>
            <option value="vacant">Свободный</option>
            <option value="archived">Архив</option>
          </select>
        </div>
      </section>

      <section class="form-section">
        <h2>Владельцы</h2>
        <p v-if="ownerships.length === 0" class="hint">Добавьте хотя бы одного владельца.</p>
        <div v-for="(row, index) in ownerships" :key="index" class="ownership-row">
          <div class="owner-search">
            <label>Владелец *</label>
            <input
              v-model="row.searchQuery"
              type="text"
              placeholder="ФИО или УНП — начните вводить для поиска"
              autocomplete="off"
              @focus="onOwnerFocus(index)"
              @input="onOwnerInput(index)"
            />
            <p class="field-hint">Выберите владельца из списка после ввода фамилии, имени или УНП</p>
            <ul v-if="row.showSuggestions" class="suggestions">
              <li
                v-for="opt in row.suggestions"
                :key="opt.id"
                @mousedown.prevent="selectOwner(index, opt)"
              >
                {{ opt.name }} <span v-if="opt.tax_id">({{ opt.tax_id }})</span>
              </li>
              <li v-if="row.suggestions.length === 0 && row.searchQuery.length >= 2" class="no-results">
                Ничего не найдено
              </li>
            </ul>
          </div>
          <div class="share-block">
            <label>Доля в участке</label>
            <select
              v-model="row.sharePresetKey"
              class="share-select"
              @change="onSharePresetChange(index, $event)"
            >
              <option
                v-for="p in SHARE_PRESETS"
                :key="p.value"
                :value="p.value"
              >
                {{ p.label }}
              </option>
              <option value="other">Другое…</option>
            </select>
            <div v-if="row.sharePresetKey === 'other'" class="share-fields share-fields-custom">
              <input
                v-model.number="row.share_numerator"
                type="number"
                min="1"
                class="share-num"
                aria-label="Числитель доли"
                placeholder="1"
                title="Числитель"
              />
              <span class="share-sep">/</span>
              <input
                v-model.number="row.share_denominator"
                type="number"
                min="1"
                class="share-den"
                aria-label="Знаменатель доли"
                placeholder="2"
                title="Знаменатель"
              />
              <span class="share-hint-inline">Напр. 1/2 — половина участка</span>
            </div>
          </div>
          <div class="primary-check">
            <label>
              <input v-model="row.is_primary" type="checkbox" />
              Основной владелец (член СТ)
            </label>
          </div>
          <div class="valid-from">
            <label>Дата начала владения *</label>
            <input v-model="row.valid_from" type="date" required />
          </div>
          <button type="button" class="btn-remove" title="Удалить" @click="removeOwnership(index)">
            ×
          </button>
        </div>
        <button type="button" class="btn-secondary" @click="addOwnership">Добавить ещё владельца</button>
      </section>

      <div v-if="validationError" class="validation-error">{{ validationError }}</div>
      <div v-if="submitError" class="validation-error">{{ submitError }}</div>

      <div class="form-actions">
        <router-link to="/land-plots" class="btn-secondary">Отмена</router-link>
        <button type="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? 'Создание…' : 'Создать участок' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { useAuthStore } from '@/stores/auth';
import type { Cooperative, Owner } from '@/types';

const SHARE_PRESETS: { value: string; label: string; num: number; den: number }[] = [
  { value: '1/1', label: 'Целиком (1/1)', num: 1, den: 1 },
  { value: '1/2', label: 'Половина (1/2)', num: 1, den: 2 },
  { value: '1/3', label: 'Треть (1/3)', num: 1, den: 3 },
  { value: '1/4', label: 'Четверть (1/4)', num: 1, den: 4 },
  { value: '2/3', label: 'Две трети (2/3)', num: 2, den: 3 },
];

interface OwnershipRow {
  owner_id: string | null;
  owner_name: string;
  searchQuery: string;
  suggestions: Owner[];
  showSuggestions: boolean;
  sharePresetKey: string;
  share_numerator: number;
  share_denominator: number;
  is_primary: boolean;
  valid_from: string;
}

const router = useRouter();
const authStore = useAuthStore();

const cooperatives = ref<Cooperative[]>([]);
const form = ref({
  cooperative_id: '' as string,
  plot_number: '',
  area_sqm: null as number | null,
  cadastral_number: '',
  status: 'active' as 'active' | 'vacant' | 'archived',
});

const ownerships = ref<OwnershipRow[]>([]);
const validationError = ref('');
const submitError = ref('');
const submitting = ref(false);

const isAdmin = computed(() => authStore.userRole === 'admin');
const currentCooperativeId = computed(() => authStore.cooperativeId ?? '');
const currentCooperativeName = computed(() => {
  const id = currentCooperativeId.value;
  if (!id) return '—';
  const c = cooperatives.value.find((x) => x.id === id);
  return c?.name ?? id;
});

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function addOwnership(): void {
  ownerships.value.push({
    owner_id: null,
    owner_name: '',
    searchQuery: '',
    suggestions: [],
    showSuggestions: false,
    sharePresetKey: '1/1',
    share_numerator: 1,
    share_denominator: 1,
    is_primary: false,
    valid_from: todayISO(),
  });
}

function onSharePresetChange(index: number, event: Event): void {
  const row = ownerships.value[index];
  if (!row) return;
  const target = event.target as HTMLSelectElement;
  const value = target?.value ?? 'other';
  row.sharePresetKey = value;
  if (value !== 'other') {
    const preset = SHARE_PRESETS.find((p) => p.value === value);
    if (preset) {
      row.share_numerator = preset.num;
      row.share_denominator = preset.den;
    }
  }
}

function removeOwnership(index: number): void {
  ownerships.value.splice(index, 1);
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null;
async function onOwnerInput(index: number): Promise<void> {
  const row = ownerships.value[index];
  if (!row) return;
  row.owner_id = null;
  row.owner_name = '';
  if (searchTimeout) clearTimeout(searchTimeout);
  if (row.searchQuery.trim().length < 2) {
    row.suggestions = [];
    row.showSuggestions = true;
    return;
  }
  searchTimeout = setTimeout((): Promise<void> => {
    return (async () => {
      try {
        const { data } = await api.get<Owner[]>('owners/search', {
          params: { q: row.searchQuery.trim(), limit: 20 },
        });
        row.suggestions = data ?? [];
        row.showSuggestions = true;
      } catch {
        row.suggestions = [];
        row.showSuggestions = true;
      }
    })();
  }, 300);
}

function onOwnerFocus(index: number): void {
  const row = ownerships.value[index];
  if (row && row.suggestions.length > 0) row.showSuggestions = true;
}

function selectOwner(index: number, owner: Owner): void {
  const row = ownerships.value[index];
  if (!row) return;
  row.owner_id = owner.id;
  row.owner_name = owner.name;
  row.searchQuery = owner.name + (owner.tax_id ? ` (${owner.tax_id})` : '');
  row.suggestions = [];
  row.showSuggestions = false;
}

function validate(): boolean {
  validationError.value = '';
  const coopId = isAdmin.value ? form.value.cooperative_id : currentCooperativeId.value;
  if (!coopId) {
    validationError.value = 'Выберите садовое товарищество.';
    return false;
  }
  if (!form.value.plot_number?.trim()) {
    validationError.value = 'Укажите номер участка.';
    return false;
  }
  const area = form.value.area_sqm;
  if (area == null || area <= 0) {
    validationError.value = 'Укажите площадь больше 0.';
    return false;
  }
  const rows = ownerships.value.filter((r) => r.owner_id);
  if (rows.length === 0) {
    validationError.value = 'Добавьте хотя бы одного владельца и выберите его из списка.';
    return false;
  }
  const primaryCount = ownerships.value.filter((r) => r.is_primary).length;
  if (primaryCount !== 1) {
    validationError.value = 'Ровно один владелец должен быть отмечен как основной (член СТ).';
    return false;
  }
  const totalShare = ownerships.value.reduce((sum, r) => {
    if (!r.owner_id) return sum;
    return sum + r.share_numerator / r.share_denominator;
  }, 0);
  if (Math.abs(totalShare - 1) > 0.001) {
    validationError.value = `Сумма долей должна быть равна 1 (сейчас ${totalShare.toFixed(2)}).`;
    return false;
  }
  return true;
}

async function onSubmit(): Promise<void> {
  submitError.value = '';
  if (!validate()) return;
  const coopId = isAdmin.value ? form.value.cooperative_id : currentCooperativeId.value;
  const payload = {
    cooperative_id: coopId,
    plot_number: form.value.plot_number.trim(),
    area_sqm: Number(form.value.area_sqm),
    cadastral_number: form.value.cadastral_number.trim() || null,
    status: form.value.status,
    ownerships: ownerships.value
      .filter((r) => r.owner_id)
      .map((r) => ({
        owner_id: r.owner_id,
        share_numerator: r.share_numerator,
        share_denominator: r.share_denominator,
        is_primary: r.is_primary,
        valid_from: r.valid_from,
      })),
  };
  submitting.value = true;
  try {
    await api.post('land-plots', payload);
    await router.push('/land-plots');
  } catch (err: unknown) {
    const msg = err && typeof err === 'object' && 'response' in err
      ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      : null;
    submitError.value = typeof msg === 'string' ? msg : 'Не удалось создать участок. Попробуйте снова.';
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
      if (currentCooperativeId.value && !form.value.cooperative_id) {
        form.value.cooperative_id = currentCooperativeId.value;
      }
    } catch {
      cooperatives.value = [];
    }
    form.value.cooperative_id = currentCooperativeId.value;
  }
  if (ownerships.value.length === 0) {
    addOwnership();
  }
});
</script>

<style scoped>
.form-view {
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  max-width: 720px;
  min-width: 0;
  overflow-x: auto;
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

.readonly-value {
  margin: 0;
  padding: 8px 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.hint {
  margin: 0 0 12px;
  font-size: 0.875rem;
  color: #6b7280;
}

.ownership-row {
  display: grid;
  grid-template-columns: minmax(0, 260px) minmax(0, 180px) minmax(0, 160px) minmax(0, 132px) 36px;
  grid-template-rows: auto auto;
  gap: 12px 16px;
  align-items: end;
  margin-bottom: 16px;
  padding: 12px;
  background: #f1f5f9;
  border-radius: 8px;
  min-width: 0;
}

.ownership-row .owner-search {
  grid-column: 1 / -1;
  grid-row: 1;
}

.ownership-row .share-block {
  grid-column: 1;
  grid-row: 2;
  position: relative;
  z-index: 11;
}

.ownership-row .primary-check {
  grid-column: 2;
  grid-row: 2;
}

.ownership-row .valid-from {
  grid-column: 3;
  grid-row: 2;
}

.ownership-row .btn-remove {
  grid-column: 5;
  grid-row: 2;
}

.field-hint {
  margin: 4px 0 0;
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.3;
}

@media (max-width: 900px) {
  .ownership-row {
    grid-template-columns: 1fr 1fr 1fr 36px;
    grid-template-rows: auto auto auto;
  }
  .ownership-row .owner-search {
    grid-column: 1 / -1;
    grid-row: 1;
  }
  .ownership-row .share-block {
    grid-column: 1 / -1;
    grid-row: 2;
  }
  .ownership-row .primary-check {
    grid-column: 1;
    grid-row: 3;
  }
  .ownership-row .valid-from {
    grid-column: 2;
    grid-row: 3;
  }
  .ownership-row .btn-remove {
    grid-column: 4;
    grid-row: 3;
  }
}

.owner-search {
  position: relative;
  min-width: 0;
}

.owner-search input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin: 0;
  padding: 0;
  list-style: none;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-height: 220px;
  overflow-y: auto;
  z-index: 10;
}

.suggestions li {
  padding: 10px 12px;
  font-size: 0.875rem;
  cursor: pointer;
}

.suggestions li:hover,
.suggestions li:focus {
  background: #f3f4f6;
}

.suggestions .no-results {
  color: #9ca3af;
  cursor: default;
}

.share-block label,
.valid-from label,
.primary-check label {
  display: block;
  margin-bottom: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
}

.share-block {
  min-width: 0;
}

.share-select {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: #fff;
  box-sizing: border-box;
}

.share-fields {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-top: 8px;
}

.share-fields-custom .share-num,
.share-fields-custom .share-den {
  width: 4rem;
  min-width: 3.5rem;
  max-width: 6rem;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9375rem;
  box-sizing: border-box;
  text-align: center;
}

.share-hint-inline {
  margin: 0;
  flex: none;
  max-width: 100%;
  font-size: 0.7rem;
  line-height: 1.35;
  color: #64748b;
  align-self: center;
}

.share-sep {
  font-weight: 600;
  color: #6b7280;
}

.valid-from input {
  width: 100%;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.primary-check {
  display: flex;
  align-items: flex-end;
  padding-bottom: 8px;
}

.primary-check label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.875rem;
}

.valid-from {
  min-width: 0;
  max-width: 132px;
}

.btn-remove {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #6b7280;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
}

.btn-remove:hover {
  background: #fef2f2;
  color: #dc2626;
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

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
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
