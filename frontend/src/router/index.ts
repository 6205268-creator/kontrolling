import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import LoginView from '@/views/LoginView.vue';
import MainLayout from '@/components/MainLayout.vue';
import DashboardView from '@/views/DashboardView.vue';
import LandPlotsView from '@/views/LandPlotsView.vue';
import LandPlotCreateView from '@/views/LandPlotCreateView.vue';
import OwnersView from '@/views/OwnersView.vue';
import AccrualsView from '@/views/AccrualsView.vue';
import AccrualCreateView from '@/views/AccrualCreateView.vue';
import PaymentsView from '@/views/PaymentsView.vue';
import PaymentCreateView from '@/views/PaymentCreateView.vue';
import ExpensesView from '@/views/ExpensesView.vue';
import MetersView from '@/views/MetersView.vue';
import ReportsView from '@/views/ReportsView.vue';
import DebtorsReportView from '@/views/DebtorsReportView.vue';
import CashFlowReportView from '@/views/CashFlowReportView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true },
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: { name: 'dashboard' } },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
        },
        {
          path: 'land-plots',
          name: 'land-plots',
          component: LandPlotsView,
        },
        {
          path: 'land-plots/create',
          name: 'land-plots-create',
          component: LandPlotCreateView,
        },
        {
          path: 'owners',
          name: 'owners',
          component: OwnersView,
        },
        {
          path: 'accruals',
          name: 'accruals',
          component: AccrualsView,
        },
        {
          path: 'accruals/create',
          name: 'accruals-create',
          component: AccrualCreateView,
        },
        {
          path: 'payments',
          name: 'payments',
          component: PaymentsView,
        },
        {
          path: 'payments/create',
          name: 'payments-create',
          component: PaymentCreateView,
        },
        {
          path: 'expenses',
          name: 'expenses',
          component: ExpensesView,
        },
        {
          path: 'meters',
          name: 'meters',
          component: MetersView,
        },
        {
          path: 'reports',
          name: 'reports',
          component: ReportsView,
          children: [
            { path: '', redirect: { name: 'reports-debtors' } },
            {
              path: 'debtors',
              name: 'reports-debtors',
              component: DebtorsReportView,
            },
          ],
        },
        {
          path: 'reports/cash-flow',
          name: 'reports-cash-flow',
          component: CashFlowReportView,
        },
      ],
    },
  ],
});

// Navigation guard для проверки аутентификации
router.beforeEach((to) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;

  if (to.meta.requiresAuth && !isAuthenticated) {
    return '/login';
  } else if (to.meta.requiresGuest && isAuthenticated) {
    return '/dashboard';
  }
});

export default router;
