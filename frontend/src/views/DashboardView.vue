<template>
  <div class="dashboard">
    <!-- Welcome Section -->
    <div class="welcome-section">
      <h1 class="dashboard-title">Добро пожаловать в Контроллинг-СТ</h1>
      <p class="dashboard-subtitle">Система учёта хозяйственной деятельности садоводческих товариществ</p>
      <p v-if="authStore.cooperativeName" class="current-cooperative">
        <span class="label">Товарищество:</span>
        <strong>{{ authStore.cooperativeName }}</strong>
      </p>
    </div>

    <!-- Metrics Cards -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon" style="background: var(--color-primary-subtle);">
            <MapPin class="metric-icon-svg" style="color: var(--color-primary);" />
          </div>
          <span class="metric-change positive">+2</span>
        </div>
        <div class="metric-value">{{ metrics.totalPlots }}</div>
        <div class="metric-label">Всего участков</div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon" style="background: var(--color-info-bg);">
            <Users class="metric-icon-svg" style="color: var(--color-info);" />
          </div>
          <span class="metric-change positive">+5</span>
        </div>
        <div class="metric-value">{{ metrics.totalOwners }}</div>
        <div class="metric-label">Владельцев</div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon" style="background: var(--color-warning-bg);">
            <AlertCircle class="metric-icon-svg" style="color: var(--color-warning);" />
          </div>
          <span class="metric-change negative">+3</span>
        </div>
        <div class="metric-value">{{ metrics.debtorsCount }}</div>
        <div class="metric-label">Должников</div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <div class="metric-icon" style="background: var(--color-success-bg);">
            <Wallet class="metric-icon-svg" style="color: var(--color-success);" />
          </div>
          <span class="metric-change positive">+12%</span>
        </div>
        <div class="metric-value">{{ metrics.collectionRate }}%</div>
        <div class="metric-label">Собрано взносов</div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-header">
          <h2 class="chart-title">Поступления по месяцам</h2>
        </div>
        <div class="chart-container">
          <Line v-if="paymentsChartData" :data="paymentsChartData" :options="chartOptions" />
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-header">
          <h2 class="chart-title">Структура расходов</h2>
        </div>
        <div class="chart-container">
          <Doughnut v-if="expensesChartData" :data="expensesChartData" :options="chartOptions" />
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions-section">
      <h2 class="section-title">Быстрые действия</h2>
      <div class="quick-actions-grid">
        <router-link to="/accruals/create" class="quick-action-btn">
          <Plus class="action-icon" />
          <span>Создать начисление</span>
        </router-link>
        <router-link to="/payments/create" class="quick-action-btn">
          <Plus class="action-icon" />
          <span>Регистрация платежа</span>
        </router-link>
        <router-link to="/expenses" class="quick-action-btn">
          <Plus class="action-icon" />
          <span>Добавить расход</span>
        </router-link>
        <router-link to="/reports" class="quick-action-btn">
          <FileText class="action-icon" />
          <span>Отчёт по должникам</span>
        </router-link>
      </div>
    </div>

    <!-- Features Grid (kept for navigation) -->
    <div class="features-section">
      <h2 class="section-title">Разделы системы</h2>
      <div class="features-grid">
        <router-link to="/land-plots" class="feature-item">
          <MapPin class="feature-icon" aria-hidden />
          <h3>Участки</h3>
          <p>Земельные участки и владельцы</p>
        </router-link>
        <router-link to="/owners" class="feature-item">
          <Users class="feature-icon" aria-hidden />
          <h3>Владельцы</h3>
          <p>Физ. и юр. лица</p>
        </router-link>
        <router-link to="/accruals" class="feature-item">
          <Wallet class="feature-icon" aria-hidden />
          <h3>Начисления</h3>
          <p>Взносы по участкам</p>
        </router-link>
        <router-link to="/payments" class="feature-item">
          <CreditCard class="feature-icon" aria-hidden />
          <h3>Платежи</h3>
          <p>Регистрация платежей</p>
        </router-link>
        <router-link to="/expenses" class="feature-item">
          <TrendingDown class="feature-icon" aria-hidden />
          <h3>Расходы</h3>
          <p>Учёт расходов СТ</p>
        </router-link>
        <router-link to="/meters" class="feature-item">
          <Gauge class="feature-icon" aria-hidden />
          <h3>Счётчики</h3>
          <p>Приборы учёта</p>
        </router-link>
        <router-link to="/reports" class="feature-item">
          <BarChart3 class="feature-icon" aria-hidden />
          <h3>Отчёты</h3>
          <p>Должники и движение средств</p>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import {
  MapPin,
  Users,
  Wallet,
  CreditCard,
  TrendingDown,
  Gauge,
  BarChart3,
  AlertCircle,
  Plus,
  FileText,
} from 'lucide-vue-next';
import { Line, Doughnut } from 'vue-chartjs';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { useAuthStore } from '@/stores/auth';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const authStore = useAuthStore();

// Demo metrics data (will be replaced with real API calls later)
const metrics = ref({
  totalPlots: 124,
  totalOwners: 98,
  debtorsCount: 15,
  collectionRate: 87,
});

// Payments chart data (demo)
const paymentsChartData = computed(() => ({
  labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
  datasets: [
    {
      label: 'Поступления 2025',
      data: [45000, 52000, 48000, 61000, 55000, 68000, 72000, 65000, 58000, 63000, 71000, 78000],
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: true,
      tension: 0.4,
    },
  ],
}));

// Expenses chart data (demo)
const expensesChartData = computed(() => ({
  labels: ['Электроэнергия', 'Вода', 'Вывоз мусора', 'Охрана', 'Уборка', 'Ремонт'],
  datasets: [
    {
      data: [35, 20, 15, 12, 10, 8],
      backgroundColor: [
        '#10b981',
        '#34d399',
        '#6ee7b7',
        '#a7f3d0',
        '#d1fae5',
        '#ecfdf5',
      ],
      borderWidth: 0,
    },
  ],
}));

// Chart options
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'bottom' as const,
      labels: {
        usePointStyle: true,
        padding: 15,
        font: {
          family: 'Manrope',
          size: 12,
        },
      },
    },
    tooltip: {
      backgroundColor: 'rgba(26, 46, 34, 0.9)',
      padding: 12,
      titleFont: {
        family: 'Manrope',
        size: 13,
      },
      bodyFont: {
        family: 'Manrope',
        size: 12,
      },
      cornerRadius: 8,
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        font: {
          family: 'Manrope',
          size: 11,
        },
      },
    },
    y: {
      grid: {
        color: 'rgba(216, 228, 220, 0.3)',
      },
      ticks: {
        font: {
          family: 'Manrope',
          size: 11,
        },
      },
    },
  },
};
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

/* Welcome Section */
.welcome-section {
  margin-bottom: 2rem;
}

.dashboard-title {
  margin: 0 0 0.5rem 0;
  font-size: var(--text-3xl);
  font-weight: var(--font-extrabold);
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.dashboard-subtitle {
  margin: 0 0 1rem 0;
  font-size: var(--text-base);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
}

.current-cooperative {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--color-primary-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.current-cooperative strong {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.metric-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
}

.metric-icon-svg {
  width: 24px;
  height: 24px;
}

.metric-change {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  border-radius: var(--radius-full);
}

.metric-change.positive {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.metric-change.negative {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.metric-value {
  font-size: var(--text-3xl);
  font-weight: var(--font-extrabold);
  color: var(--color-text);
  line-height: 1;
  margin-bottom: 0.25rem;
}

.metric-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-weight: var(--font-medium);
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.chart-header {
  margin-bottom: 1.5rem;
}

.chart-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.chart-container {
  height: 280px;
  position: relative;
}

/* Quick Actions */
.quick-actions-section {
  margin-bottom: 2rem;
}

.section-title {
  margin: 0 0 1.5rem 0;
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.quick-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  color: var(--color-text);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  text-decoration: none;
  transition: all var(--transition-base);
}

.quick-action-btn:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.action-icon {
  width: 20px;
  height: 20px;
  color: var(--color-primary);
}

/* Features Section */
.features-section {
  margin-bottom: 2rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

.feature-item {
  padding: 1.5rem 1.25rem;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  text-align: center;
  transition: all var(--transition-base);
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  box-shadow: var(--shadow-sm);
}

.feature-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}

.feature-icon {
  width: 2.25rem;
  height: 2.25rem;
  color: var(--color-primary);
  flex-shrink: 0;
}

.feature-item h3 {
  margin: 0;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.feature-item p {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: var(--leading-tight);
}

/* Responsive */
@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .quick-actions-grid {
    grid-template-columns: 1fr;
  }
  
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
