import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Payment, FinancialSubject, Owner } from '@/types';
import api from '@/services/api';

export interface PaymentCreate {
  financial_subject_id: string;
  payer_owner_id: string;
  amount: number;
  payment_date: string;
  document_number?: string;
  description?: string;
}

export const usePaymentsStore = defineStore('payments', () => {
  const payments = ref<Payment[]>([]);
  const financialSubjects = ref<FinancialSubject[]>([]);
  const owners = ref<Owner[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchPayments(cooperativeId?: string | null): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const params: Record<string, string> = {};
      if (cooperativeId) {
        params.cooperative_id = cooperativeId;
      }
      const response = await api.get<Payment[]>('payments/', { params });
      payments.value = response.data ?? [];
    } catch (e: unknown) {
      const message = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Не удалось загрузить список платежей';
      error.value = typeof message === 'string' ? message : 'Ошибка загрузки';
      payments.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchFinancialSubjects(cooperativeId: string): Promise<void> {
    try {
      const response = await api.get<FinancialSubject[]>('financial-subjects/', {
        params: { cooperative_id: cooperativeId },
      });
      financialSubjects.value = response.data ?? [];
    } catch {
      financialSubjects.value = [];
    }
  }

  async function searchFinancialSubjects(query: string, cooperativeId: string): Promise<FinancialSubject[]> {
    try {
      const response = await api.get<FinancialSubject[]>('financial-subjects/', {
        params: { cooperative_id: cooperativeId, search: query },
      });
      return response.data ?? [];
    } catch {
      return [];
    }
  }

  async function fetchOwners(cooperativeId?: string | null): Promise<void> {
    try {
      const params: Record<string, string> = {};
      if (cooperativeId) {
        params.cooperative_id = cooperativeId;
      }
      const response = await api.get<Owner[]>('owners/', { params });
      owners.value = response.data ?? [];
    } catch {
      owners.value = [];
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

  async function registerPayment(data: PaymentCreate): Promise<Payment> {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.post<Payment>('payments/', data);
      return response.data;
    } catch (e: unknown) {
      const message = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Не удалось зарегистрировать платёж';
      error.value = typeof message === 'string' ? message : 'Ошибка регистрации';
      throw new Error(error.value);
    } finally {
      loading.value = false;
    }
  }

  async function cancelPayment(paymentId: string): Promise<Payment> {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.post<Payment>(`payments/${paymentId}/cancel`);
      return response.data;
    } catch (e: unknown) {
      const message = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Не удалось отменить платёж';
      error.value = typeof message === 'string' ? message : 'Ошибка отмены';
      throw new Error(error.value);
    } finally {
      loading.value = false;
    }
  }

  return {
    payments,
    financialSubjects,
    owners,
    loading,
    error,
    fetchPayments,
    fetchFinancialSubjects,
    searchFinancialSubjects,
    fetchOwners,
    searchOwners,
    registerPayment,
    cancelPayment,
  };
});
