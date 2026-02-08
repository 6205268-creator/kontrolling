# Диаграммы архитектуры КОНТРОЛЛИНГ

На GitHub диаграммы ниже рендерятся нативно (Mermaid).

## 1. Акторы (actors)

```mermaid
flowchart TB
    subgraph Actors["Actors"]
        Person_Sobstvennik["Person_Sobstvennik"]
        Person_Predsedatel_ST["Person_Predsedatel_ST"]
        Person_Buhgalter_ST["Person_Buhgalter_ST"]
    end
```

## 2. Внешние системы (external_systems)

```mermaid
flowchart TB
    subgraph ExternalSystems["External Systems"]
        System_BelarusBankAPI["System_BelarusBankAPI"]
        System_TelegramBot["System_TelegramBot"]
        System_EmailService["System_EmailService"]
    end
```

## 3. Базы данных (databases)

```mermaid
flowchart TB
    subgraph Databases["Databases"]
        Database_PostgreSQL_ST["Database_PostgreSQL_ST<br/>Требование РБ: хранение 5+ лет"]
    end
```

## 4. System Context L1 (system-context-l1)

```mermaid
flowchart LR
    subgraph Actors["Акторы"]
        Person_Sobstvennik["Собственник участка"]
        Person_Predsedatel_ST["Председатель СТ"]
        Person_Kaznachey_ST["Казначей СТ"]
    end

    subgraph External["Внешние системы"]
        System_Bank["Банк\nвыписки"]
        System_Telegram["Telegram"]
        System_Email_RB["Почта РБ"]
        System_SMS["SMS"]
    end

    System_Kontrolling["«КОНТРОЛЛИНГ»"]

    Person_Sobstvennik -->|получает уведомления| System_Kontrolling
    System_Kontrolling --> Person_Sobstvennik
    System_Bank -->|поставляет выписки| System_Kontrolling
    Person_Predsedatel_ST -->|формирует отчёты| System_Kontrolling
    Person_Kaznachey_ST -->|формирует отчёты| System_Kontrolling
    System_Kontrolling --> System_Telegram
    System_Kontrolling --> System_Email_RB
    System_Kontrolling --> System_SMS
```

## 5. Container L2 — Банковские выписки (container-diagram)

```mermaid
flowchart LR
    subgraph External["Внешние системы"]
        System_BelarusBankAPI["System_BelarusBankAPI"]
    end

    subgraph Containers["Контейнеры"]
        Service_BankingReconciliation["Service_BankingReconciliation<br/>Python"]
        Service_ContributionManager["Service_ContributionManager"]
    end

    Database_PostgreSQL_ST["Database_PostgreSQL_ST"]

    System_BelarusBankAPI -->|выписка| Service_BankingReconciliation
    Service_BankingReconciliation -->|распознавание плательщика| Service_BankingReconciliation
    Service_BankingReconciliation -->|зачисление| Service_BankingReconciliation
    Service_BankingReconciliation -->|PaymentProcessed| Service_ContributionManager
    Service_BankingReconciliation <--> Database_PostgreSQL_ST
```
