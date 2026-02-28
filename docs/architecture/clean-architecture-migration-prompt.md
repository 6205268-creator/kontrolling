## Роль
Ты — Senior Python/Django Architect. Твоя задача: рефакторинг backend/ в модульную Clean Architecture БЕЗ потери функциональности.

## Контекст проекта
- Система: Controlling (учёт СТ в Беларуси)
- Технологический стек: Django 5.x, PostgreSQL 15+, Python 3.11+
- Ключевая концепция: FinancialSubject — ядро всех финансовых операций
- Мультитенантность: все сущности фильтруются по cooperative_id

backend/
├── modules/
│ ├── shared/
│ │ ├── kernel/
│ │ │ ├── entities.py # BaseEntity, ValueObject
│ │ │ ├── repositories.py # IRepository (ABC)
│ │ │ ├── exceptions.py # DomainError, ValidationError
│ │ │ └── events.py # DomainEvent base class
│ │ └── multitenancy/
│ │ └── middleware.py # cooperative_id из контекста
│ │
│ ├── cooperative_core/
│ │ ├── domain/
│ │ │ ├── entities.py # Cooperative (pure Python, NO Django)
│ │ │ ├── repositories.py # ICooperativeRepository (ABC)
│ │ │ └── services.py # Domain Services
│ │ ├── application/
│ │ │ ├── dtos.py # CreateCooperativeDTO, etc.
│ │ │ ├── use_cases.py # CreateCooperativeUseCase
│ │ │ └── validators.py # Business validation
│ │ ├── infrastructure/
│ │ │ ├── models.py # CooperativeModel (Django ORM)
│ │ │ ├── repositories.py # CooperativeRepository (реализация)
│ │ │ └── signals.py # Django signals
│ │ └── api/
│ │ ├── views.py # DRF ViewSets
│ │ ├── serializers.py # ModelSerializer
│ │ └── urls.py
│ │
│ ├── land_management/
│ │ ├── domain/
│ │ │ ├── entities.py # LandPlot, Owner, PlotOwnership
│ │ │ ├── repositories.py # ILandPlotRepository, IOwnerRepository
│ │ │ └── services.py # PlotOwnershipService
│ │ ├── application/
│ │ │ ├── dtos.py
│ │ │ ├── use_cases.py # CreateLandPlotUseCase, TransferOwnershipUseCase
│ │ │ └── events.py # LandPlotCreated, OwnerChanged
│ │ ├── infrastructure/
│ │ │ ├── models.py # LandPlotModel, OwnerModel, PlotOwnershipModel
│ │ │ ├── repositories.py # Реализации репозиториев
│ │ │ └── signals.py # Публикация Domain Events
│ │ └── api/
│ │ ├── views.py
│ │ ├── serializers.py
│ │ └── urls.py
│ │
│ ├── financial_core/
│ │ ├── domain/
│ │ │ ├── entities.py # FinancialSubject, Balance
│ │ │ ├── repositories.py # IFinancialSubjectRepository
│ │ │ └── services.py # BalanceCalculator (domain logic)
│ │ ├── application/
│ │ │ ├── dtos.py
│ │ │ ├── use_cases.py # CreateFinancialSubjectUseCase, CalculateBalanceUseCase
│ │ │ └── events.py # FinancialSubjectCreated, BalanceUpdated
│ │ ├── infrastructure/
│ │ │ ├── models.py # FinancialSubjectModel
│ │ │ ├── repositories.py
│ │ │ └── signals.py
│ │ └── api/
│ │ └── (если нужен API для FinancialSubject)
│ │
│ ├── accruals/
│ │ ├── domain/
│ │ │ ├── entities.py # Accrual
│ │ │ └── repositories.py # IAccrualRepository
│ │ ├── application/
│ │ │ ├── dtos.py
│ │ │ ├── use_cases.py # CreateAccrualUseCase, ApplyAccrualUseCase
│ │ │ └── events.py # AccrualCreated, AccrualApplied
│ │ ├── infrastructure/
│ │ │ ├── models.py # AccrualModel (с django-simple-history)
│ │ │ └── repositories.py
│ │ └── api/
│ │ ├── views.py
│ │ ├── serializers.py
│ │ └── urls.py
│ │
│ ├── payments/
│ │ ├── domain/
│ │ │ ├── entities.py # Payment
│ │ │ └── repositories.py
│ │ ├── application/
│ │ │ ├── use_cases.py # CreatePaymentUseCase, CancelPaymentUseCase
│ │ │ └── events.py # PaymentRegistered, PaymentCancelled
│ │ ├── infrastructure/
│ │ │ ├── models.py # PaymentModel (с django-simple-history)
│ │ │ └── repositories.py
│ │ └── api/
│ │ ├── views.py
│ │ ├── serializers.py
│ │ └── urls.py
│ │
│ ├── meters/
│ │ ├── domain/
│ │ │ ├── entities.py # Meter, MeterReading
│ │ │ └── repositories.py
│ │ ├── application/
│ │ │ ├── use_cases.py # RecordMeterReadingUseCase
│ │ │ └── events.py # MeterReadingRecorded
│ │ ├── infrastructure/
│ │ │ ├── models.py
│ │ │ └── repositories.py
│ │ └── api/
│ │ ├── views.py
│ │ ├── serializers.py
│ │ └── urls.py
│ │
│ ├── expenses/
│ │ ├── domain/
│ │ │ ├── entities.py # Expense, ExpenseCategory
│ │ │ └── repositories.py
│ │ ├── application/
│ │ │ ├── use_cases.py # CreateExpenseUseCase
│ │ │ └── events.py # ExpenseRegistered
│ │ ├── infrastructure/
│ │ │ ├── models.py # ExpenseModel (с django-simple-history)
│ │ │ └── repositories.py
│ │ └── api/
│ │ ├── views.py
│ │ ├── serializers.py
│ │ └── urls.py
│ │
│ └── reporting/
│ ├── domain/
│ │ └── services.py # ReportGenerator (domain logic)
│ ├── application/
│ │ └── use_cases.py # GenerateDebtorReportUseCase
│ ├── infrastructure/
│ │ └── (если нужны специфичные query)
│ └── api/
│ ├── views.py
│ └── urls.py
│
├── core/
│ ├── settings.py
│ ├── urls.py # Главный router, включает модули
│ └── wsgi.py
│
└── manage.py

---

## ПРАВИЛА СЛОЁВ (STRICT)

### 1. Domain Layer (modules/{module}/domain/)
**ЗАПРЕЩЕНО:**
- `import django` (никаких Django ORM, Models, Views)
- Импортировать из application, infrastructure, api
- Импортировать из других модулей

### 2. Application Layer (modules/{module}/application/)
МОЖЕТ:
Импортировать из domain текущего модуля
Импортировать из modules/shared/
Содержать Use Cases, DTOs, валидацию
ЗАПРЕЩЕНО:
Импортировать из infrastructure (Django ORM)
Импортировать из api
Импортировать из других модулей напрямую (только через Domain Events)
Пример:
python
1234567891011121314
# ПРАВИЛЬНО ✅
from modules.financial_core.domain.entities import FinancialSubject
from modules.financial_core.domain.repositories import IFinancialSubjectRepository
from modules.shared.kernel.exceptions import DomainError

class CreatePaymentUseCase:
    def __init__(self, fs_repo: IFinancialSubjectRepository):
        self.fs_repo = fs_repo
    
    def execute(self, fs_id: UUID, amount: Decimal, payer_id: UUID):

### 3. Infrastructure Layer (modules/{module}/infrastructure/)
МОЖЕТ:
Django ORM, Models, Signals
Импортировать из domain и application текущего модуля
Реализовывать репозитории
ЗАПРЕЩЕНО:
Импортировать из api
Импортировать модели из других модулей напрямую
Пример:
python
123456789101112131415161718192021222324252627282930
# ПРАВИЛЬНО ✅
from django.db import models
from simple_history.models import HistoricalRecords
from modules.financial_core.domain.entities import FinancialSubject as DomainEntity

class FinancialSubjectModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    subject_type = models.CharField(max_length=50)
    subject_id = models.UUIDField()
    cooperative_id = models.UUIDField(db_index=True)

### 4. API Layer (modules/{module}/api/)
МОЖЕТ:
DRF Views, Serializers
Импортировать из application и infrastructure текущего модуля
Пример:
python
123456789101112131415
from rest_framework import viewsets
from modules.payments.application.use_cases import CreatePaymentUseCase
from modules.payments.infrastructure.repositories import PaymentRepository
from .serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    def create(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        

КРИТИЧЕСКИЕ ПРАВИЛА ИЗ PROJECT-DESIGN.MD

1. FinancialSubject — ядро финансов
ПРАВИЛО: Accrual и Payment ссылаются ТОЛЬКО на financial_subject_id
ЗАПРЕЩЕНО: Прямые связи Payment → LandPlot, Accrual → Meter
Проверка:
python
12345678
# НЕПРАВИЛЬНО ❌
class PaymentModel(models.Model):
    land_plot = models.ForeignKey(LandPlotModel, on_delete=models.CASCADE)  # ЗАПРЕЩЕНО!

# ПРАВИЛЬНО ✅
class PaymentModel(models.Model):
    financial_subject = models.ForeignKey(FinancialSubjectModel, on_delete=models.CASCADE)
    payer_owner = models.ForeignKey(OwnerModel, on_delete=models.CASCADE)

2. Мультитенантность
ПРАВИЛО: Все модели с cooperative_id должны иметь:
cooperative_id = models.UUIDField(db_index=True)
Все query: .filter(cooperative_id=...)
Проверка в репозиториях:
python
1234567
# ПРАВИЛЬНО ✅
class PaymentRepository:
    def get_by_id(self, id: UUID, cooperative_id: UUID) -> Payment:
        obj = PaymentModel.objects.get(id=id, cooperative_id=cooperative_id)
        return obj.to_domain()
    
    # ЗАПРЕЩЕНО: PaymentModel.objects.get(id=id) без cooperative_id!

3. Историзация
ПРАВИЛО: Для PlotOwnership, Accrual, Payment, Expense:
python
12345
from simple_history.models import HistoricalRecords

class PaymentModel(models.Model):
    # ... поля
    history = HistoricalRecords()
4. Межмодульное взаимодействие
ПРАВИЛО: Модули не импортируют друг друга напрямую
НЕПРАВИЛЬНО:
python
12
# modules/accruals/application/use_cases.py
from modules.land_management.infrastructure.models import LandPlotModel  # ЗАПРЕЩЕНО!
ПРАВИЛЬНО (через Domain Events):
python
1234567891011121314151617181920212223242526272829303132
# modules/land_management/domain/events.py
class LandPlotCreatedEvent(DomainEvent):
    land_plot_id: UUID
    cooperative_id: UUID
    plot_number: str

# modules/land_management/infrastructure/signals.py
from django.db.models.signals import post_save
from modules.shared.kernel.events import publish_event


ПОШАГОВЫЙ ПЛАН МИГРАЦИИ

- Шаг 1: Создать базовую структуру
Создать папку backend/modules/
Создать backend/modules/shared/kernel/ с базовыми классами
Создать __init__.py во всех папках
- Шаг 2: Мигрировать Cooperative Core (самый простой модуль)
domain/entities.py → Cooperative (pure Python dataclass)
domain/repositories.py → ICooperativeRepository (ABC)
infrastructure/models.py → CooperativeModel (Django)
infrastructure/repositories.py → CooperativeRepository (реализация)
application/use_cases.py → CreateCooperativeUseCase
api/views.py → CooperativeViewSet
- Шаг 3: Мигрировать Land Management
domain/entities.py → LandPlot, Owner, PlotOwnership
infrastructure/models.py → с django-simple-history для PlotOwnership
Создать Domain Events: LandPlotCreated, OwnerChanged
infrastructure/signals.py → публикация событий
- Шаг 4: Мигрировать Financial Core
domain/entities.py → FinancialSubject, Balance
infrastructure/models.py → FinancialSubjectModel
ВАЖНО: Убедиться, что нет прямых связей с LandPlot/Meter
- Шаг 5: Мигрировать Accruals и Payments
domain/entities.py → Accrual, Payment
infrastructure/models.py → с django-simple-history
ВАЖНО: Только financial_subject_id, НЕ land_plot_id!
application/use_cases.py → CreateAccrualUseCase, CreatePaymentUseCase
- Шаг 6: Мигрировать Meters, Expenses, Reporting
Аналогично предыдущим шагам
- Шаг 7: Настроить роутинг
core/urls.py → включить routers из всех модулей
Проверить, что все API endpoints работают
- Шаг 8: Тестирование
Запустить migrations
Проверить, что все query фильтруются по cooperative_id
Проверить историзацию (django-simple-history)
ЗАПРЕТЫ (STRICT)
НЕЛЬЗЯ создавать модели в корне backend/ (только в modules/{module}/infrastructure/)
НЕЛЬЗЯ импортировать Django в domain слой
НЕЛЬЗЯ создавать прямые связи Payment → LandPlot (только через FinancialSubject)
НЕЛЬЗЯ забывать cooperative_id в фильтрах
НЕЛЬЗЯ импортировать модели из другого модуля напрямую
НЕЛЬЗЯ удалять финансовые записи (только status='cancelled')
ПРОВЕРКА ПОСЛЕ МИГРАЦИИ
После завершения миграции, проверь:
✅ Все модели в backend/modules/{module}/infrastructure/models.py
✅ Domain слой не импортирует Django
✅ FinancialSubject используется во всех финансовых операциях
✅ Все query имеют .filter(cooperative_id=...)
✅ PlotOwnership, Accrual, Payment, Expense имеют history = HistoricalRecords()
✅ Межмодульное взаимодействие через Domain Events
✅ manage.py работает, migrations применяются
НАЧАЛО РАБОТЫ
Сначала покажи мне план: какие файлы создашь/переместишь
Дождись подтверждения
Выполняй шаг за шагом
После каждого шага — краткий отчёт: что сделано, какие файлы созданы
Если встречаешь проблему — остановись и спроси
ЯЗЫК ОТВЕТА: Русский (объяснения), код — английский (PEP 8)
ВАЖНО
Если текущий код в backend/ отличается от описанного в project-design.md:
Сначала проанализируй существующие модели
Предложи план маппинга на новую структуру
Не теряй данные при рефакторинге
Сохрани все существующие поля и связи
ГОТОВ? Начни с анализа текущей структуры backend/ и предложи план миграции.


Используй и то тоже 
alwaysApply: true
description: "Чистая архитектура, модульность по bounded context, независимое развитие модулей разными командами"
globs:
  - "src/**"
---

# Архитектура уровней
- Всю бизнес-логику располагать в слое domain (entities, use cases).
- В слое application размещать фасады/интерactors, оркестрацию и политики.
- В слоях infrastructure / adapters только реализацию интерфейсов, IO (БД, HTTP, очереди).
- Запрещены зависимости:
  - из domain в application/infrastructure;
  - из application в UI/transport напрямую, только через интерфейсы/DTO.

# Модульность и команды
- Код делится на независимые модули по bounded context (каталог, заказы, биллинг и т.д.).
- Каждый модуль имеет свой слой domain/application/infrastructure внутри себя.
- Межмодульные связи только через явно определённые интерфейсы или события (domain events, integration events).
- Нельзя использовать внутренние классы/таблицы другого модуля напрямую.

# Контракты и API
- Все публичные API модулей описаны контрактами (OpenAPI/протоколы/интерфейсы).
- Изменения контрактов делаются обратно совместимыми; при невозможности – версияция.
- Любой новый модуль обязан декларировать входы/выходы, не лезть в чужие базы.

# Эволюция и расширение
- Новая функциональность добавляется сначала в domain/use cases, потом в адаптеры.
- Рефакторинг: сначала покрыть ключевые сценарии тестами (см. testing.mdc), потом менять реализацию, сохраняя контракты.
- Запрещено повторно использовать чужие «удобные» функции, если они привязывают к реализации другого модуля – вынести в общий контракт или shared-kernel.

# Инфраструктура и монорепо
- Структура монорепы и пайплайны CI/CD должны позволять:
  - отдельную сборку/деплой модулей;
  - проверки зависимостей между модулями (см. monorepo.mdc, ci-cd.mdc).
- Любые срезы по архитектуре (domain/application/infrastructure) должны быть очевидны по структуре каталогов и названиям.