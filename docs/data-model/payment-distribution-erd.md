# ER-диаграмма: модуль Payment Distribution

**Назначение:** Модель данных модуля распределения платежей (Member, лицевые счета, распределение по долгам).  
**Связано:** [ADR 0003](../architecture/adr/0003-payment-distribution-model.md), [payment-distribution-continue.md](../tasks/payment-distribution-continue.md).

## Сущности модуля

| Таблица | Описание |
|--------|----------|
| `members` | Член СТ (связь Owner ↔ Cooperative) |
| `member_plots` | Участки члена СТ (Member ↔ LandPlot, доля) |
| `personal_accounts` | Лицевой счёт члена |
| `personal_account_transactions` | Операции по лицевому счёту (зачисление, распределение) |
| `payment_distributions` | Распределение платежа по виду долга (Payment → FinancialSubject) |
| `settings_modules` | Модуль настроек СТ (приоритеты, тарифы) |
| `payment_distribution_rules` | Правила приоритета распределения |
| `contribution_type_settings` | Настройки видов взносов по модулю |
| `meter_tariffs` | Тарифы по типам счётчиков |

## Диаграмма (Mermaid ER)

```mermaid
erDiagram
    cooperatives ||--o{ members : "has"
    owners ||--o{ members : "is_member"
    members ||--o| personal_accounts : "has"
    members ||--o{ member_plots : "has"
    land_plots ||--o{ member_plots : "linked"

    personal_accounts ||--o{ personal_account_transactions : "has"
    payments ||--o{ personal_account_transactions : "credits"
    payment_distributions ||--o| personal_account_transactions : "recorded_as"

    payments ||--o{ payment_distributions : "distributed_as"
    financial_subjects ||--o{ payment_distributions : "receives"

    cooperatives ||--o{ settings_modules : "has"
    settings_modules ||--o{ payment_distribution_rules : "has"
    settings_modules ||--o{ contribution_type_settings : "has"
    settings_modules ||--o{ meter_tariffs : "has"
    contribution_types ||--o{ payment_distribution_rules : "rule_for"
    contribution_types ||--o{ contribution_type_settings : "configured_in"

    members {
        uuid id PK
        uuid owner_id FK
        uuid cooperative_id FK
        string status
        datetime joined_date
        datetime created_at
        datetime updated_at
    }

    member_plots {
        uuid id PK
        uuid member_id FK
        uuid land_plot_id FK
        int share_numerator
        int share_denominator
        bool is_primary
        datetime created_at
    }

    personal_accounts {
        uuid id PK
        uuid member_id FK
        uuid cooperative_id FK
        string account_number UK
        decimal balance
        string status
        datetime opened_at
        datetime closed_at
    }

    personal_account_transactions {
        uuid id PK
        uuid account_id FK
        uuid payment_id FK
        uuid distribution_id FK
        string transaction_number
        datetime transaction_date
        decimal amount
        string type
        string description
    }

    payment_distributions {
        uuid id PK
        uuid payment_id FK
        uuid financial_subject_id FK
        string distribution_number
        datetime distributed_at
        decimal amount
        int priority
        string status
    }

    settings_modules {
        uuid id PK
        uuid cooperative_id FK
        string module_name
        bool is_active
    }

    payment_distribution_rules {
        uuid id PK
        uuid settings_module_id FK
        string rule_type
        int priority
        uuid contribution_type_id FK
        string meter_type
        bool is_active
    }

    contribution_type_settings {
        uuid id PK
        uuid settings_module_id FK
        uuid contribution_type_id FK
        decimal default_amount
        bool is_mandatory
        string calculation_period
    }

    meter_tariffs {
        uuid id PK
        uuid settings_module_id FK
        string meter_type
        decimal tariff_per_unit
        datetime valid_from
        datetime valid_to
    }
```

## Связи с другими модулями

- **cooperative_core:** `cooperatives` — Member, PersonalAccount, SettingsModule привязаны к СТ.
- **land_management:** `owners`, `land_plots` — Member связан с Owner; MemberPlot — с LandPlot.
- **financial_core:** `financial_subjects` — PaymentDistribution зачисляет сумму на FinancialSubject.
- **payments:** `payments` — платёж зачисляется на лицевой счёт и распределяется через PaymentDistribution.
- **accruals:** `contribution_types` — правила и настройки видов взносов.
