import { test, expect, Page } from '@playwright/test';

/**
 * E2E тесты полного пользовательского флоу:
 * Логин → Создание участка → Создание начисления → Регистрация платежа → Проверка баланса
 */

// Тестовые данные
const TEST_USER = {
  username: 'testuser',
  password: 'testpassword123',
};

const TEST_LAND_PLOT = {
  plotNumber: 'E2E-001',
  area: '500',
  cadastralNumber: 'E2E/CAD/001',
};

const TEST_ACCRUAL = {
  amount: '150.00',
  description: 'E2E тестовое начисление',
};

const TEST_PAYMENT = {
  amount: '100.00',
  documentNumber: 'E2E-PAY-001',
};

/**
 * Вспомогательная функция для логина
 */
async function login(page: Page) {
  await page.goto('/login');

  // Заполняем форму логина
  await page.fill('input[name="username"], input[type="text"]', TEST_USER.username);
  await page.fill('input[name="password"], input[type="password"]', TEST_USER.password);

  // Отправляем форму
  await page.click('button[type="submit"], button:has-text("Войти"), button:has-text("Login")');

  // Ждём редирект на dashboard
  await page.waitForURL(/\/dashboard|\/$/, { timeout: 10000 });

  // Проверяем что залогинены
  const url = page.url();
  expect(url).toMatch(/\/dashboard|\/$/);
}

/**
 * Сценарий 1: Полный флоу - создание участка, начисления, платежа и проверка баланса
 */
test.describe('E2E Full Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Логин перед каждым тестом
    await login(page);
  });

  test('should complete full flow: login → create land plot → create accrual → register payment → check balance', async ({
    page,
  }) => {
    // Шаг 1: Переход на страницу участков
    await page.goto('/land-plots');
    await expect(page).toHaveURL(/\/land-plots/);

    // Шаг 2: Создание участка
    await page.click('button:has-text("Добавить"), button:has-text("Создать"), a:has-text("Добавить участок")');
    await page.waitForURL(/\/land-plots\/create/);

    // Заполняем форму участка
    await page.fill('input[name="plot_number"], input[placeholder*="номер"]', TEST_LAND_PLOT.plotNumber);
    await page.fill('input[name="area_sqm"], input[placeholder*="площадь"]', TEST_LAND_PLOT.area);
    await page.fill(
      'input[name="cadastral_number"], input[placeholder*="кадастр"]',
      TEST_LAND_PLOT.cadastralNumber,
    );

    // Выбираем статус (если есть select)
    await page.selectOption('select[name="status"]', 'active').catch(() => {});

    // Отправляем форму
    await page.click('button[type="submit"], button:has-text("Создать"), button:has-text("Сохранить")');

    // Ждём редирект на список участков
    await page.waitForURL(/\/land-plots/);

    // Проверяем что участок создан
    await expect(page.locator(`text=${TEST_LAND_PLOT.plotNumber}`)).toBeVisible();

    // Шаг 3: Переход на страницу начислений
    await page.goto('/accruals');
    await expect(page).toHaveURL(/\/accruals/);

    // Шаг 4: Создание начисления
    await page.click('button:has-text("Добавить"), button:has-text("Создать"), a:has-text("Создать начисление")');
    await page.waitForURL(/\/accruals\/create/);

    // Заполняем форму начисления
    await page.fill('input[name="amount"], input[placeholder*="сумма"]', TEST_ACCRUAL.amount);
    await page.fill('input[name="description"], textarea[placeholder*="описание"]', TEST_ACCRUAL.description);

    // Выбираем дату (если есть)
    const today = new Date().toISOString().split('T')[0];
    await page.fill('input[name="accrual_date"], input[type="date"]', today).catch(() => {});

    // Отправляем форму
    await page.click('button[type="submit"], button:has-text("Создать"), button:has-text("Сохранить")');

    // Ждём редирект или подтверждение
    await page.waitForTimeout(2000);

    // Проверяем что начисление создано
    await expect(page.locator(`text=${TEST_ACCRUAL.amount}`)).toBeVisible();

    // Шаг 5: Переход на страницу платежей
    await page.goto('/payments');
    await expect(page).toHaveURL(/\/payments/);

    // Шаг 6: Регистрация платежа
    await page.click('button:has-text("Добавить"), button:has-text("Создать"), a:has-text("Зарегистрировать платёж")');
    await page.waitForURL(/\/payments\/create/);

    // Заполняем форму платежа
    await page.fill('input[name="amount"], input[placeholder*="сумма"]', TEST_PAYMENT.amount);
    await page.fill(
      'input[name="document_number"], input[placeholder*="документ"]',
      TEST_PAYMENT.documentNumber,
    );

    // Отправляем форму
    await page.click('button[type="submit"], button:has-text("Зарегистрировать"), button:has-text("Сохранить")');

    // Ждём редирект или подтверждение
    await page.waitForTimeout(2000);

    // Проверяем что платёж создан
    await expect(page.locator(`text=${TEST_PAYMENT.documentNumber}`)).toBeVisible();

    // Шаг 7: Проверка отчёта по должникам
    await page.goto('/reports/debtors');
    await expect(page).toHaveURL(/\/reports\/debtors/);

    // Проверяем что отчёт загружен
    await expect(page.locator('table')).toBeVisible();
  });

  test('should view debtors report', async ({ page }) => {
    // Переход на страницу отчётов
    await page.goto('/reports/debtors');
    await expect(page).toHaveURL(/\/reports\/debtors/);

    // Проверяем наличие таблицы с должниками
    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Проверяем заголовки таблицы
    const headers = page.locator('th');
    const headerCount = await headers.count();
    expect(headerCount).toBeGreaterThan(0);
  });

  test('should view cash flow report', async ({ page }) => {
    // Переход на страницу отчёта о движении средств
    await page.goto('/reports/cash-flow');
    await expect(page).toHaveURL(/\/reports\/cash-flow/);

    // Проверяем наличие формы выбора периода
    await expect(page.locator('input[type="date"]')).toBeVisible();
  });
});

/**
 * Сценарий 2: Тесты навигации и авторизации
 */
test.describe('Navigation and Auth', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    // Пытаемся попасть на защищённую страницу
    await page.goto('/land-plots');

    // Должен быть редирект на login
    await page.waitForURL(/\/login/);
    await expect(page).toHaveURL(/\/login/);
  });

  test('should logout successfully', async ({ page }) => {
    // Логин
    await login(page);

    // Проверка что на dashboard
    await expect(page).toHaveURL(/\/dashboard|\/$/);

    // Выход
    await page.click('button:has-text("Выйти"), button:has-text("Logout"), .user-menu button');

    // Должен быть редирект на login
    await page.waitForURL(/\/login/);
    await expect(page).toHaveURL(/\/login/);
  });

  test('should navigate through all main sections', async ({ page }) => {
    // Логин
    await login(page);

    // Навигация по основным разделам
    const sections = [
      { name: 'Участки', url: /\/land-plots/ },
      { name: 'Владельцы', url: /\/owners/ },
      { name: 'Начисления', url: /\/accruals/ },
      { name: 'Платежи', url: /\/payments/ },
      { name: 'Расходы', url: /\/expenses/ },
      { name: 'Счётчики', url: /\/meters/ },
      { name: 'Отчёты', url: /\/reports/ },
    ];

    for (const section of sections) {
      // Клик по пункту меню
      await page.click(`nav a:has-text("${section.name}"), .sidebar a:has-text("${section.name}")`);

      // Ждём перехода
      await page.waitForURL(section.url);

      // Проверяем что страница загрузилась
      expect(page.url()).toMatch(section.url);
    }
  });
});

/**
 * Сценарий 3: Тесты создания сущностей
 */
test.describe('Entity Creation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should create owner', async ({ page }) => {
    // Переход на страницу владельцев
    await page.goto('/owners');

    // Клик по кнопке создания
    await page.click('button:has-text("Добавить"), button:has-text("Создать")');

    // Заполняем форму владельца
    const ownerData = {
      name: 'E2E Тестовый Владелец',
      email: 'e2e-owner@test.com',
      taxId: 'E2E123456',
    };

    await page.fill('input[name="name"], input[placeholder*="имя"]', ownerData.name);
    await page.fill('input[name="contact_email"], input[placeholder*="email"]', ownerData.email);
    await page.fill('input[name="tax_id"], input[placeholder*="УНП"]', ownerData.taxId);

    // Отправляем форму
    await page.click('button[type="submit"], button:has-text("Создать"), button:has-text("Сохранить")');

    // Ждём подтверждения
    await page.waitForTimeout(2000);

    // Проверяем что владелец создан
    await expect(page.locator(`text=${ownerData.name}`)).toBeVisible();
  });

  test('should view meters', async ({ page }) => {
    // Переход на страницу счётчиков
    await page.goto('/meters');
    await expect(page).toHaveURL(/\/meters/);

    // Проверяем наличие таблицы
    await expect(page.locator('table')).toBeVisible();
  });

  test('should view expenses', async ({ page }) => {
    // Переход на страницу расходов
    await page.goto('/expenses');
    await expect(page).toHaveURL(/\/expenses/);

    // Проверяем наличие таблицы
    await expect(page.locator('table')).toBeVisible();
  });
});
