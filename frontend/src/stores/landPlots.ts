import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { LandPlotWithOwners } from '@/types';
import api from '@/services/api';

export const useLandPlotsStore = defineStore('landPlots', () => {
  const plots = ref<LandPlotWithOwners[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchPlots(cooperativeId?: string | null): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const params: Record<string, string> = {};
      if (cooperativeId) {
        params.cooperative_id = cooperativeId;
      }
      const response = await api.get<LandPlotWithOwners[]>('land-plots/', { params });
      plots.value = response.data ?? [];
    } catch (e: unknown) {
      const message = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : 'Не удалось загрузить список участков';
      error.value = typeof message === 'string' ? message : 'Ошибка загрузки';
      plots.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function createPlot(data: {
    cooperative_id: string;
    plot_number: string;
    area_sqm: number;
    cadastral_number?: string;
    status: string;
    ownerships: Array<{
      owner_id: string;
      share_numerator: number;
      share_denominator: number;
      is_primary: boolean;
      valid_from: string;
    }>;
  }): Promise<LandPlotWithOwners> {
    const response = await api.post<LandPlotWithOwners>('land-plots/', data);
    return response.data;
  }

  return {
    plots,
    loading,
    error,
    fetchPlots,
    createPlot,
  };
});
