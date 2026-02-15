# Minimal entity set (v1)

**Минимальный набор сущностей (ядро v1)**
Entity names in **English**; Russian meaning in comments (EN → RU в комментариях).

**Мультитенантность:** `cooperative_id` у LandPlot, FinancialSubject, Expense. Владелец (Owner) с СТ напрямую не связан — к товариществу идём через участок (LandPlot → Cooperative). Владение участком задаётся только через PlotOwnership (участок, владелец, период, доля); участок без владельца — нет записей PlotOwnership на нужную дату.

---

## 1. Cooperative

**RU:** Садоводческое товарищество (СТ). Одна запись = одно товарищество. Используется как tenant при мультитенантности.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор СТ |
| name | varchar | Название товарищества |
| unp | varchar | УНП (учётный номер плательщика) |
| address | varchar | Адрес (опционально) |

---

## 2. Owner

**RU:** Владелец. Абстрактная сущность: владелец участка или счётчика может быть **физическим лицом**, **юридическим лицом** (напр. исполком) или участок может быть **без владельца** (нет записей PlotOwnership на нужную дату). С СТ владелец напрямую не связан — к товариществу идём через участок (LandPlot → Cooperative). Тип владельца задаётся в owner_type.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор владельца |
| owner_type | varchar | Тип: physical (физ. лицо), legal (юр. лицо) |
| name | varchar | Наименование (ФИО или название орг.) |
| tax_id | varchar | УНП или ИД физлица (опционально) |
| contact_phone | varchar | Телефон (опционально) |
| contact_email | varchar | Электронная почта (опционально) |

---

## 3. LandPlot

**RU:** Земельный участок. Принадлежит одному СТ (cooperative_id). Владение задаётся только через PlotOwnership (участок без владельца — нет записей на нужную дату). Прямая связь LandPlot → Owner **отсутствует**.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| cooperative_id | uuid | СТ (FK) |
| plot_number | varchar | Номер участка |
| area_sqm | decimal | Площадь, кв. м |
| cadastral_number | varchar | Кадастровый номер (опц.) |
| status | varchar | active / vacant / archived |

---

## 4. PlotOwnership

**RU:** Право/доля собственности на участок. Связь участок ↔ владелец с периодом (valid_from, valid_to) и долей (дробь). По дате можно определить, кто владел участком и какой долей; допускается несколько владельцев в один период (доли в сумме = 1). Поле `is_primary` определяет основного владельца — члена СТ.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| land_plot_id | uuid | Участок (FK) |
| owner_id | uuid | Владелец (FK) |
| share_numerator | int | Числитель доли (напр. 1) |
| share_denominator | int | Знаменатель доли (1 = вся доля, 2 = 1/2, 3 = 1/3) |
| is_primary | boolean | Основной владелец = член СТ (один на участок) |
| valid_from | date | Дата регистрации в системе (когда СТ узнало о смене) |
| valid_to | date | Конец периода (опц.; пусто — действует по сей день) |

---

## 5. Meter

**RU:** Счётчик (прибор учёта). Привязан к **владельцу (Owner)** (owner_id). Финансовые операции — через FinancialSubject (subject_type = WATER_METER / ELECTRICITY_METER).

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор счётчика |
| owner_id | uuid | Владелец счётчика (FK) |
| number | varchar | Номер счётчика |
| meter_type | varchar | Тип: water, electricity, gas… |
| installation_date | date | Дата установки (опц.) |
| status | varchar | active / decommissioned |

---

## 6. FinancialSubject

**RU:** Центр финансовой ответственности. Финансовая проекция любого бизнес-объекта, способного генерировать долг. Все начисления и оплаты агрегируются на уровне FinancialSubject — финансовые документы **никогда не ссылаются напрямую** на участок, счётчик и т.д. Комбинация subject_type + subject_id уникальна в рамках одного СТ.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| subject_type | varchar | LAND_PLOT, WATER_METER, ELECTRICITY_METER, GENERAL_DECISION |
| subject_id | uuid | ID записи в таблице бизнес-объекта (FK по типу) |
| cooperative_id | uuid | СТ (FK) |
| code | varchar | Уникальный код для платёжных документов |
| status | varchar | active / closed |
| created_at | datetime | Дата создания |

---

## 7. ContributionType

**RU:** Вид взноса. Справочник: членский, целевой и т.д. Используется в Accrual для типизации начислений.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| code | varchar | Код (напр. membership, target) |
| name | varchar | Название (напр. «Членский взнос») |

---

## 8. Payment

**RU:** Платёж. Факт оплаты по финансовому субъекту. К СТ — через FinancialSubject. Долг принадлежит FinancialSubject; деньги — плательщику. Платёж сразу фиксируется как подтверждённый (черновиков нет).

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| financial_subject_id | uuid | Центр финансовой ответственности (FK) |
| payer_owner_id | uuid | Плательщик (Owner, FK), опц. |
| amount | decimal | Сумма, BYN |
| payment_date | date | Дата оплаты |
| document_number | varchar | Номер платёжного документа извне (опц.) |
| description | varchar | Описание (опционально) |
| status | varchar | confirmed / cancelled |

---

## 9. Accrual

**RU:** Начисление. Начисленная сумма по финансовому субъекту за период (взнос, услуга). К СТ — через FinancialSubject. Отменённое начисление не «исправляется» — создаётся новое.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| financial_subject_id | uuid | Центр финансовой ответственности (FK) |
| contribution_type_id | uuid | Вид взноса (FK) |
| amount | decimal | Сумма, BYN |
| accrual_date | date | Дата начисления |
| period_start | date | Начало периода |
| period_end | date | Конец периода (опц.) |
| status | varchar | created / applied / cancelled |

---

## 10. MeterReading

**RU:** Показание счётчика. Одно значение: счётчик, дата, показание.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| meter_id | uuid | Счётчик (FK) |
| value | decimal | Значение показания |
| reading_date | date | Дата снятия показания |

---

## 11. ExpenseCategory

**RU:** Категория расходов СТ. Справочник: дороги, зарплата, материалы и т.д.

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| code | varchar | Код категории |
| name | varchar | Название (напр. «Ремонт дорог») |

---

## 12. Expense

**RU:** Расход СТ. Операция казначейства, **не привязана к FinancialSubject** — это отдельный финансовый поток (расходы СТ как юрлица).

| Attribute (EN) | Type | Comment (RU) |
|---|---|---|
| id | uuid | Уникальный идентификатор |
| cooperative_id | uuid | СТ (FK) |
| category_id | uuid | Категория расхода (FK) |
| created_by | uuid | Кто создал (FK, пользователь/казначей) |
| amount | decimal | Сумма, BYN |
| expense_date | date | Дата расхода |
| document_number | varchar | Номер платёжного поручения/чека (опц.) |
| description | varchar | Описание |

---

## Relationships (связи)

| From (EN) | To (EN) | Cardinality | Comment (RU) |
|---|---|---|---|
| Cooperative | LandPlot | 1 : N | В СТ много участков |
| Cooperative | FinancialSubject | 1 : N | В СТ много финансовых субъектов |
| Cooperative | Expense | 1 : N | В СТ много расходов |
| LandPlot | PlotOwnership | 1 : N | У участка много записей права/доли |
| Owner | PlotOwnership | 1 : N | У владельца много записей по участкам |
| Owner | Meter | 1 : N | У владельца может быть несколько счётчиков |
| FinancialSubject | Payment | 1 : N | По финансовому субъекту много платежей |
| FinancialSubject | Accrual | 1 : N | По финансовому субъекту много начислений |
| Owner | Payment | 1 : N | Плательщик (payer_owner_id), опционально |
| ContributionType | Accrual | 1 : N | По виду взноса много начислений |
| ExpenseCategory | Expense | 1 : N | По категории много расходов |
| Meter | MeterReading | 1 : N | По счётчику много показаний |

**FinancialSubject → бизнес-объект:** связь полиморфная — subject_type определяет таблицу, subject_id — конкретную запись (LandPlot, Meter, и т.д.).

**Balance (баланс)** — не сущность. Считается: сумма начислений по FinancialSubject минус сумма платежей по FinancialSubject.

---

## Planned for later (добавим позже)

- Линия (ряд/улица)
- Касса, банковские счета, банковские операции
- Собрания, решения собраний (как сущности; финансовая часть покрыта через FinancialSubject с типом GENERAL_DECISION)
- Общее имущество СТ
- Первичные документы
- Аудит (журнал операций), отчётность (Report)
- Член СТ (Member) как отдельная сущность — на данный момент членство определяется через `PlotOwnership.is_primary`

---

*Диаграмма для просмотра в браузере: `docs/data-model/schema-viewer.html`.*
