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

    <DataTable
      v-else
      :data="filteredPlots"
      :columns="columns"
      :pagination="true"
      :page-size="10"
      search-placeholder="Поиск участков..."
      empty-message="Нет участков"
      @row-click="handleRowClick"
    >
      <!-- Filters slot -->
      <template #filters>
        <div v-if="isAdmin" class="filter-group">
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
      </template>

      <!-- Custom cell renderers -->
      <template #cell-status="{ value }">
        <span :class="['badge', `badge-${getStatusType(value as string)}`]">
          {{ statusLabel(value as string) }}
        </span>
      </template>

      <template #cell-owners="{ value }">
        <span class="owners-cell">
          <Users class="owners-icon" />
          {{ value }}
        </span>
      </template>

      <template #cell-actions="{ item }">
        <div class="actions-cell">
          <router-link
            :to="`/land-plots/${(item as any).id}/edit`"
            class="btn-icon-link"
            title="Редактировать"
          >
            <Edit2 class="action-icon" aria-hidden />
          </router-link>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Plus, AlertCircle, Edit2, Users } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useLandPlotsStore } from '@/stores/landPlots';
import type { Cooperative } from '@/types';
import api from '@/services/api';
import DataTable from '@/components/DataTable.vue';

const authStore = useAuthStore();
const landPlotsStore = useLandPlotsStore();

const cooperatives = ref<Cooperative[]>([]);
const selectedCooperativeId = ref<string>('');

const isAdmin = computed(() => authStore.userRole === 'admin');
const canCreate = computed(() => authStore.isAuthenticated);

// Table columns
const columns = [
  { key: 'plot_number', label: 'Номер участка', sortable: true },
  { key: 'area_sqm', label: 'Площадь, м²', sortable: true, format: 'number' as const },
  { key: 'status', label: 'Статус', sortable: true },
  { key: 'owners', label: 'Владельцы', sortable: false },
  { key: 'actions', label: 'Действия', sortable: false },
];

// Filtered plots
const filteredPlots = computed(() => {
  const plots = landPlotsStore.plots.map((plot) => ({
    ...plot,
    area_sqm: plot.area_sqm,
    status: plot.status,
    owners: ownersSummary(plot.owners),
  }));
  
  return plots;
});

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    active: 'success',
    vacant: 'info',
    archived: 'warning',
  };
  return types[status] || 'info';
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: 'Действующий',
    vacant: 'Свободный',
    archived: 'Архивный',
  };
  return labels[status] ?? status;
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

function handleRowClick(item: unknown) {
  // Could navigate to edit page or show details
  console.log('Row clicked:', item);
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

.view-header {
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  background: var(--color-bg-card);
  color: var(--color-text);
  cursor: pointer;
}

.btn-icon {
  width: 1.125rem;
  height: 1.125rem;
}

.btn-icon-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.375rem;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.btn-icon-link:hover {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.action-icon {
  width: 1rem;
  height: 1rem;
}

.owners-cell {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.owners-icon {
  width: 0.875rem;
  height: 0.875rem;
}

.actions-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.error-message {
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-radius: var(--radius-md);
  padding: 1rem 1rem;
  margin-bottom: 1rem;
  color: var(--color-error);
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
}
</style>
