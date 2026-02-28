<template>
  <div class="land-plots-view">
    <header class="view-header">
      <h1>Участки</h1>
      <router-link
        v-if="canCreate"
        to="/land-plots/create"
        class="btn btn-primary"
      >
        <Plus class="btn-icon" aria-hidden />
        Добавить участок
      </router-link>
    </header>

    <div v-if="isAdmin" class="filter-bar">
      <label for="cooperative-filter">СТ:</label>
      <select
        id="cooperative-filter"
        v-model="selectedCooperativeId"
        class="filter-select"
        @change="onFilterChange"
      >
        <option value="">Все СТ</option>
        <option
          v-for="c in cooperatives"
          :key="c.id"
          :value="c.id"
        >
          {{ c.name }}
        </option>
      </select>
    </div>

    <div v-if="landPlotsStore.error" class="error-message">
      <div class="error-summary">
        <AlertCircle class="error-icon" aria-hidden />
        <strong>{{ landPlotsStore.error.summary }}</strong>
      </div>
      <div v-if="landPlotsStore.error.details" class="error-details">
        {{ landPlotsStore.error.details }}
      </div>
    </div>

    <div v-if="landPlotsStore.loading" class="loading">Загрузка…</div>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Номер участка</th>
            <th>Площадь, м²</th>
            <th>Статус</th>
            <th>Владельцы</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="landPlotsStore.plots.length === 0">
            <td colspan="4" class="empty">Нет участков</td>
          </tr>
          <tr
            v-for="plot in landPlotsStore.plots"
            :key="plot.id"
          >
            <td>{{ plot.plot_number }}</td>
            <td>{{ formatArea(plot.area_sqm) }}</td>
            <td>{{ statusLabel(plot.status) }}</td>
            <td>{{ ownersSummary(plot.owners) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Plus, AlertCircle } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useLandPlotsStore } from '@/stores/landPlots';
import type { Cooperative } from '@/types';
import api from '@/services/api';

const authStore = useAuthStore();
const landPlotsStore = useLandPlotsStore();

const cooperatives = ref<Cooperative[]>([]);
const selectedCooperativeId = ref<string>('');

const isAdmin = computed(() => authStore.userRole === 'admin');
const canCreate = computed(() =>
  authStore.userRole === 'admin' || authStore.userRole === 'treasurer'
);

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: 'Действующий',
    vacant: 'Свободный',
    archived: 'Архивный',
  };
  return labels[status] ?? status;
}

function formatArea(sqm: number): string {
  return Number(sqm).toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function ownersSummary(owners: { is_primary: boolean }[]): string {
  if (!owners?.length) return '—';
  const primary = owners.filter((o) => o.is_primary).length;
  if (owners.length === 1) return primary ? '1 (основной)' : '1';
  return `${owners.length} (основных: ${primary})`;
}

function onFilterChange(): void {
  loadPlots();
}

function loadPlots(): void {
  if (isAdmin.value && selectedCooperativeId.value) {
    landPlotsStore.fetchPlots(selectedCooperativeId.value);
  } else {
    landPlotsStore.fetchPlots(authStore.cooperativeId ?? undefined);
  }
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
  }
  loadPlots();
});
</script>

<style scoped>
.land-plots-view {
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
}

.filter-bar label {
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.btn-icon {
  width: 1.125rem;
  height: 1.125rem;
}

.error-message {
  background: var(--color-bg-danger);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  padding: 1rem 1rem;
  margin-bottom: 1rem;
  color: var(--color-text-danger);
}

.error-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-base);
}

.error-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.error-details {
  margin-top: 0.5rem;
  margin-left: 1.75rem;
  font-size: var(--text-sm);
  opacity: 0.9;
  font-family: var(--font-mono);
}
</style>
