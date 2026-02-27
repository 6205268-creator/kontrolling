import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Accrual } from '@/types';
import api from '@/services/api';

export interface AccrualCreatePayload {
  financial_subject_id: string;
  contribution_type_id: string;
  amount: number;
  accrual_date: string;
  period_start: string;
  period_end?: string;
}

export const useAccrualsStore = defineStore('accruals', () => {
  const accruals = ref<Accrual[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchAccruals(params: {
    financial_subject_id?: string;
    cooperative_id?: string;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const query: Record<string, string> = {};
      if (params.financial_subject_id) query.financial_subject_id = params.financial_subject_id;
      if (params.cooperative_id) query.cooperative_id = params.cooperative_id;
      const { data } = await api.get<Accrual[]>('accruals/', { params: query });
      accruals.value = data ?? [];
    } catch (e: unknown) {
      const message =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : 'Не удалось загрузить начисления';
      error.value = typeof message === 'string' ? message : 'Ошибка загрузки';
      accruals.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function createAccrual(payload: AccrualCreatePayload): Promise<Accrual> {
    const { data } = await api.post<Accrual>('accruals/', payload);
    return data!;
  }

  async function applyAccrual(id: string): Promise<Accrual> {
    const { data } = await api.post<Accrual>(`accruals/${id}/apply`);
    return data!;
  }

  async function cancelAccrual(id: string): Promise<Accrual> {
    const { data } = await api.post<Accrual>(`accruals/${id}/cancel`);
    return data!;
  }

  return {
    accruals,
    loading,
    error,
    fetchAccruals,
    createAccrual,
    applyAccrual,
    cancelAccrual,
  };
});
