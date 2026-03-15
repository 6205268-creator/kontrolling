# ADR 0003: Модель распределения платежей (Payment Distribution)

**Статус:** Принято  
**Дата:** 2026-03-15  
**Контекст:** Продолжение разработки модуля payment_distribution (см. docs/tasks/payment-distribution-continue.md).

## Контекст

В системе учёта СТ платёж от владельца должен распределяться по видам задолженности (членские взносы, целевые, счётчики и т.д.) согласно правилам приоритета. Требовалась доменная модель и API для:

- членства в СТ (Member) и лицевых счетов (PersonalAccount);
- регистрации платежа и зачисления на лицевой счёт;
- распределения платежа по начислениям по правилам (PaymentDistributionRule);
- отмены платежа и корректировок.

Модуль должен интегрироваться с существующими модулями: cooperative_core, land_management, financial_core, payments, accruals — без дублирования сущностей Payment/Accrual, через обратные relationships и при необходимости адаптеры репозиториев.

## Решение

1. **Модуль payment_distribution** в backend/app/modules/payment_distribution по слоям Clean Architecture: domain (entities, repositories), application (use_cases, dtos), infrastructure (models, repositories), api (routes, schemas).

2. **Новые сущности и таблицы:** Member, MemberPlot, PersonalAccount, PersonalAccountTransaction, PaymentDistribution, SettingsModule, PaymentDistributionRule, ContributionTypeSettings, MeterTariff. Связи с Cooperative, Owner, LandPlot, Payment, FinancialSubject, ContributionType через FK и обратные relationships со строковыми ссылками (избежание циклических импортов).

3. **Use Cases:** CreateMemberUseCase (создание члена и лицевого счёта), ReceivePaymentUseCase, DistributePaymentUseCase, CancelPaymentUseCase и др. — с зависимостями от репозиториев и EventDispatcher.

4. **API:** все эндпоинты защищены JWT (get_current_user). Для роли treasurer — доступ только к своему cooperative_id; для admin — любой СТ. Первый реализованный эндпоинт: POST /api/payment-distribution/members (интеграция с CreateMemberUseCase).

5. **Интеграция:** эндпоинты получают сессию через get_db, создают репозитории модуля (MemberRepository, PersonalAccountRepository и т.д.) и вызывают use cases. Адаптеры к Payment/Accrual/FinancialSubject (другие модули) — при реализации ReceivePayment и DistributePayment.

## Последствия

- Единая точка входа для логики «платёж → лицевой счёт → распределение по долгам».
- Обратные relationships в cooperative_core, land_management, financial_core, payments, accruals требуют TYPE_CHECKING импортов из payment_distribution для аннотаций.
- Тесты модуля могут запускаться отдельно (собственный conftest с test_db, admin_token, sample_cooperative, sample_owner).
- Дальнейшая реализация: адаптеры IPaymentRepository/IAccrualRepository/IFinancialSubjectRepository для полного цикла распределения платежа.
