import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { DebtorInfo, CashFlowReport } from '@/types';
import api from '@/services/api';

export const useReportsStore = defineStore('reports', () => {
  const debtorsReport = ref<DebtorInfo[]>([]);
  const cashFlowReport = ref<CashFlowReport | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchDebtorsReport(cooperativeId: string, minDebt: number = 0): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.get<DebtorInfo[]>('reports/debtors', {
        params: { cooperative_id: cooperativeId, min_debt: minDebt },
      });
      debtorsReport.value = response.data ?? [];
    } catch (e: unknown) {
      const message = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Ошибка загрузки отчёта по должникам';
      error.value = typeof message === 'string' ? message : 'Ошибка загрузки отчёта по должникам';
      debtorsReport.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchCashFlowReport(
    cooperativeId: string,
    periodStart: string,
    periodEnd: string
  ): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.get<CashFlowReport>('reports/cash-flow', {
        params: {
          cooperative_id: cooperativeId,
          period_start: periodStart,
          period_end: periodEnd,
        },
      });
      cashFlowReport.value = response.data ?? null;
    } catch (e: unknown) {
      const message = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Ошибка загрузки отчёта о движении средств';
      error.value = typeof message === 'string' ? message : 'Ошибка загрузки отчёта о движении средств';
      cashFlowReport.value = null;
    } finally {
      loading.value = false;
    }
  }

  return {
    debtorsReport,
    cashFlowReport,
    loading,
    error,
    fetchDebtorsReport,
    fetchCashFlowReport,
  };
});
