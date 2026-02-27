// Пользователь
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'chairman' | 'treasurer';
  cooperative_id: string | null;
  is_active: boolean;
}

// Токен аутентификации
export interface Token {
  access_token: string;
  token_type: string;
}

// Данные для входа
export interface LoginCredentials {
  username: string;
  password: string;
}

// Cooperative (СТ)
export interface Cooperative {
  id: string;
  name: string;
  unp?: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

// Owner (владелец)
export interface Owner {
  id: string;
  owner_type: 'physical' | 'legal';
  name: string;
  tax_id?: string;
  contact_phone?: string;
  contact_email?: string;
  created_at: string;
  updated_at: string;
}

// LandPlot (участок)
export interface LandPlot {
  id: string;
  cooperative_id: string;
  plot_number: string;
  area_sqm: number;
  cadastral_number?: string;
  status: 'active' | 'vacant' | 'archived';
  created_at: string;
  updated_at: string;
}

// Участок с владельцами (ответ API списка/детали)
export interface LandPlotWithOwners extends LandPlot {
  owners: PlotOwnership[];
  financial_subject_id: string | null;
  financial_subject_code: string | null;
}

// PlotOwnership (право собственности)
export interface PlotOwnership {
  id: string;
  land_plot_id: string;
  owner_id: string;
  share_numerator: number;
  share_denominator: number;
  is_primary: boolean;
  valid_from: string;
  valid_to?: string;
  created_at: string;
}

// FinancialSubject (финансовый субъект)
export interface FinancialSubject {
  id: string;
  subject_type: 'LAND_PLOT' | 'WATER_METER' | 'ELECTRICITY_METER' | 'GENERAL_DECISION';
  subject_id: string;
  cooperative_id: string;
  code: string;
  status: 'active' | 'closed';
  created_at: string;
}

// ContributionType (вид взноса)
export interface ContributionType {
  id: string;
  name: string;
  code: string;
  description?: string;
  created_at: string;
}

// Accrual (начисление)
export interface Accrual {
  id: string;
  financial_subject_id: string;
  contribution_type_id: string;
  amount: number;
  accrual_date: string;
  period_start: string;
  period_end?: string;
  status: 'created' | 'applied' | 'cancelled';
  created_at: string;
  updated_at: string;
}

// Payment (платёж)
export interface Payment {
  id: string;
  financial_subject_id: string;
  payer_owner_id: string;
  amount: number;
  payment_date: string;
  document_number?: string;
  description?: string;
  status: 'confirmed' | 'cancelled';
  created_at: string;
  updated_at: string;
}

// Expense (расход)
export interface Expense {
  id: string;
  cooperative_id: string;
  category_id: string;
  amount: number;
  expense_date: string;
  document_number?: string;
  description?: string;
  status: 'created' | 'confirmed' | 'cancelled';
  created_at: string;
  updated_at: string;
}

// ExpenseCategory (категория расходов)
export interface ExpenseCategory {
  id: string;
  name: string;
  code: string;
  description?: string;
  created_at: string;
}

// Meter (счётчик)
export interface Meter {
  id: string;
  owner_id: string;
  meter_type: 'WATER' | 'ELECTRICITY';
  serial_number?: string;
  installation_date?: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

// MeterReading (показание счётчика)
export interface MeterReading {
  id: string;
  meter_id: string;
  reading_value: number;
  reading_date: string;
  created_at: string;
}

// Balance (баланс финансового субъекта)
export interface Balance {
  financial_subject_id: string;
  total_accruals: number;
  total_payments: number;
  balance: number;
  subject_type: string;
  subject_id: string;
  cooperative_id: string;
  code: string;
}

// Отчёты

// Должник (для отчёта по должникам)
export interface DebtorInfo {
  financial_subject_id: string;
  subject_type: string;
  subject_info: Record<string, unknown>;
  owner_name: string;
  total_debt: number;
}

// Отчёт о движении средств за период
export interface CashFlowReport {
  period_start: string;
  period_end: string;
  total_accruals: number;
  total_payments: number;
  total_expenses: number;
  net_balance: number;
}
