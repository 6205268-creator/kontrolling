import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Owner } from '@/types';
import api from '@/services/api';

export const useOwnersStore = defineStore('owners', () => {
  const owners = ref<Owner[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchOwners(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.get<Owner[]>('owners/');
      owners.value = response.data ?? [];
    } catch (e: unknown) {
      const message = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Не удалось загрузить список владельцев';
      error.value = typeof message === 'string' ? message : 'Ошибка загрузки';
      owners.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function searchOwners(query: string): Promise<Owner[]> {
    try {
      const params = query ? { q: query } : {};
      const response = await api.get<Owner[]>('owners/search', { params });
      return response.data ?? [];
    } catch {
      return [];
    }
  }

  async function createOwner(data: {
    owner_type: 'physical' | 'legal';
    name: string;
    tax_id?: string;
    contact_phone?: string;
    contact_email?: string;
  }): Promise<Owner> {
    const response = await api.post<Owner>('owners/', data);
    return response.data;
  }

  return {
    owners,
    loading,
    error,
    fetchOwners,
    searchOwners,
    createOwner,
  };
});
