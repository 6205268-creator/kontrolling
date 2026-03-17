<template>
  <div class="owners-view">
    <header class="view-header">
      <h1>Владельцы</h1>
      <Button
        v-if="canCreate"
        label="Добавить владельца"
        icon="pi pi-plus"
        @click="showCreateModal = true"
      />
    </header>

    <div class="search-bar">
      <label for="search">Поиск:</label>
      <InputText
        id="search"
        v-model="searchQuery"
        placeholder="По имени или УНП"
        class="search-input-pv"
        @input="onSearch"
      />
    </div>

    <Message v-if="ownersStore.error" severity="error" :closable="false">
      {{ ownersStore.error }}
    </Message>

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

    <Dialog
      v-model:visible="showCreateModal"
      modal
      header="Новый владелец"
      :style="{ width: 'min(520px, 100%)' }"
      :dismissable-mask="true"
      @hide="createError = null"
    >
      <form id="owner-create-form" @submit.prevent="onCreateOwner" class="dialog-form">
        <div class="form-group">
          <label for="owner_type">Тип владельца:</label>
          <Select
            id="owner_type"
            v-model="newOwner.owner_type"
            :options="ownerTypeOptions"
            option-label="label"
            option-value="value"
            placeholder="Выберите тип"
            class="w-full"
          />
        </div>
        <div class="form-group">
          <label for="name">Имя / Название:</label>
          <InputText
            id="name"
            v-model="newOwner.name"
            required
            placeholder="ФИО или название организации"
            class="w-full"
          />
        </div>
        <div class="form-group">
          <label for="tax_id">УНП:</label>
          <InputText
            id="tax_id"
            v-model="newOwner.tax_id"
            placeholder="УНП (опционально)"
            class="w-full"
          />
        </div>
        <div class="form-group">
          <label for="contact_phone">Телефон:</label>
          <InputText
            id="contact_phone"
            v-model="newOwner.contact_phone"
            placeholder="+375 XX XXX XX XX"
            class="w-full"
          />
        </div>
        <div class="form-group">
          <label for="contact_email">Email:</label>
          <InputText
            id="contact_email"
            v-model="newOwner.contact_email"
            type="email"
            placeholder="email@example.com"
            class="w-full"
          />
        </div>
        <Message v-if="createError" severity="error" :closable="false">
          {{ createError }}
        </Message>
      </form>
      <template #footer>
        <Button label="Отмена" severity="secondary" @click="showCreateModal = false" />
        <Button type="submit" form="owner-create-form" label="Создать" :loading="creating" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';
import Dialog from 'primevue/dialog';
import Message from 'primevue/message';
import { useAuthStore } from '@/stores/auth';
import { useOwnersStore } from '@/stores/owners';
import type { Owner } from '@/types';

const ownerTypeOptions: { label: string; value: 'physical' | 'legal' }[] = [
  { label: 'Физическое лицо', value: 'physical' },
  { label: 'Юридическое лицо', value: 'legal' },
];

const authStore = useAuthStore();
const ownersStore = useOwnersStore();

const searchQuery = ref('');
const filteredOwners = ref<Owner[]>([]);
let searchDebounce: ReturnType<typeof setTimeout> | null = null;
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

const canCreate = computed(() => authStore.isAuthenticated);

function ownerTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    physical: 'Физ. лицо',
    legal: 'Юр. лицо',
  };
  return labels[type] ?? type;
}

function onSearch(): void {
  if (searchDebounce) clearTimeout(searchDebounce);
  searchDebounce = setTimeout(async () => {
    if (searchQuery.value.trim()) {
      filteredOwners.value = await ownersStore.searchOwners(searchQuery.value);
    } else {
      filteredOwners.value = [...ownersStore.owners];
    }
  }, 300);
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

.search-input-pv {
  min-width: 260px;
}

.dialog-form .form-group {
  margin-bottom: 1rem;
}
.dialog-form .form-group label {
  display: block;
  margin-bottom: 0.375rem;
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
  color: var(--color-text);
}
.dialog-form .w-full {
  width: 100%;
}
</style>
