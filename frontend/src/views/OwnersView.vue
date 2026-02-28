<template>
  <div class="owners-view">
    <header class="view-header">
      <h1>Владельцы</h1>
      <button
        v-if="canCreate"
        class="btn btn-primary"
        type="button"
        @click="showCreateModal = true"
      >
        <UserPlus class="btn-icon" aria-hidden />
        Добавить владельца
      </button>
    </header>

    <div class="search-bar">
      <label for="search">Поиск:</label>
      <input
        id="search"
        v-model="searchQuery"
        type="text"
        placeholder="По имени или УНП"
        class="search-input"
        @input="onSearch"
      />
    </div>

    <p v-if="ownersStore.error" class="error-message">
      {{ ownersStore.error }}
    </p>

    <div v-if="ownersStore.loading" class="loading">Загрузка…</div>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Имя</th>
            <th>Тип</th>
            <th>УНП</th>
            <th>Телефон</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredOwners.length === 0">
            <td colspan="5" class="empty">Нет владельцев</td>
          </tr>
          <tr
            v-for="owner in filteredOwners"
            :key="owner.id"
          >
            <td>{{ owner.name }}</td>
            <td>{{ ownerTypeLabel(owner.owner_type) }}</td>
            <td>{{ owner.tax_id || '—' }}</td>
            <td>{{ owner.contact_phone || '—' }}</td>
            <td>{{ owner.contact_email || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модалка создания владельца -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>Новый владелец</h2>
          <button class="close-btn" @click="showCreateModal = false">&times;</button>
        </div>
        <form @submit.prevent="onCreateOwner">
          <div class="form-group">
            <label for="owner_type">Тип владельца:</label>
            <select id="owner_type" v-model="newOwner.owner_type" required class="form-select">
              <option value="physical">Физическое лицо</option>
              <option value="legal">Юридическое лицо</option>
            </select>
          </div>
          <div class="form-group">
            <label for="name">Имя / Название:</label>
            <input
              id="name"
              v-model="newOwner.name"
              type="text"
              required
              class="form-input"
              placeholder="ФИО или название организации"
            />
          </div>
          <div class="form-group">
            <label for="tax_id">УНП:</label>
            <input
              id="tax_id"
              v-model="newOwner.tax_id"
              type="text"
              class="form-input"
              placeholder="УНП (опционально)"
            />
          </div>
          <div class="form-group">
            <label for="contact_phone">Телефон:</label>
            <input
              id="contact_phone"
              v-model="newOwner.contact_phone"
              type="text"
              class="form-input"
              placeholder="+375 XX XXX XX XX"
            />
          </div>
          <div class="form-group">
            <label for="contact_email">Email:</label>
            <input
              id="contact_email"
              v-model="newOwner.contact_email"
              type="email"
              class="form-input"
              placeholder="email@example.com"
            />
          </div>
          <p v-if="createError" class="error-message">{{ createError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">
              Отмена
            </button>
            <button type="submit" class="btn btn-primary" :disabled="creating">
              {{ creating ? 'Создание...' : 'Создать' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { UserPlus } from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useOwnersStore } from '@/stores/owners';
import type { Owner } from '@/types';

const authStore = useAuthStore();
const ownersStore = useOwnersStore();

const searchQuery = ref('');
const filteredOwners = ref<Owner[]>([]);
const showCreateModal = ref(false);
const createError = ref<string | null>(null);
const creating = ref(false);

const newOwner = ref<{
  owner_type: 'physical' | 'legal';
  name: string;
  tax_id?: string;
  contact_phone?: string;
  contact_email?: string;
}>({
  owner_type: 'physical',
  name: '',
  tax_id: '',
  contact_phone: '',
  contact_email: '',
});

const canCreate = computed(() =>
  authStore.userRole === 'admin' || authStore.userRole === 'treasurer'
);

function ownerTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    physical: 'Физ. лицо',
    legal: 'Юр. лицо',
  };
  return labels[type] ?? type;
}

async function onSearch(): Promise<void> {
  if (searchQuery.value.trim()) {
    filteredOwners.value = await ownersStore.searchOwners(searchQuery.value);
  } else {
    filteredOwners.value = [...ownersStore.owners];
  }
}

async function onCreateOwner(): Promise<void> {
  createError.value = null;
  creating.value = true;
  try {
    const data = {
      owner_type: newOwner.value.owner_type,
      name: newOwner.value.name,
      tax_id: newOwner.value.tax_id || undefined,
      contact_phone: newOwner.value.contact_phone || undefined,
      contact_email: newOwner.value.contact_email || undefined,
    };
    await ownersStore.createOwner(data);
    showCreateModal.value = false;
    await ownersStore.fetchOwners();
    searchQuery.value = '';
    filteredOwners.value = [...ownersStore.owners];
    resetForm();
  } catch (e: unknown) {
    const message = e && typeof e === 'object' && 'response' in e
      ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
      : 'Не удалось создать владельца';
    createError.value = typeof message === 'string' ? message : 'Ошибка создания';
  } finally {
    creating.value = false;
  }
}

function resetForm(): void {
  newOwner.value = {
    owner_type: 'physical',
    name: '',
    tax_id: '',
    contact_phone: '',
    contact_email: '',
  };
}

onMounted(async () => {
  await ownersStore.fetchOwners();
  filteredOwners.value = [...ownersStore.owners];
});
</script>

<style scoped>
.owners-view {
  padding: 1.5rem;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.btn-icon {
  width: 1.125rem;
  height: 1.125rem;
}
</style>
