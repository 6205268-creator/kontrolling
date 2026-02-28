# System Patterns

## 🏗️ Архитектурные паттерны

### Clean Architecture (Backend)

**Уровни**:

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │  ← modules/*/api/routes.py
├─────────────────────────────────────────┤
│       Application (Use Cases)           │  ← modules/*/application/use_cases.py
├─────────────────────────────────────────┤
│          Domain (Entities)              │  ← modules/*/domain/entities.py
├─────────────────────────────────────────┤
│      Infrastructure (SQLAlchemy)        │  ← modules/*/infrastructure/models.py
└─────────────────────────────────────────┘
```

**Принципы**:
- Domain слой не зависит от фреймворков
- Зависимости направлены внутрь
- Repository pattern для доступа к данным
- Domain Events для межмодульного взаимодействия

**Модули (Bounded Contexts)**:
- `cooperative_core` — управление СТ
- `land_management` — участки и владельцы
- `financial_core` — финансовые субъекты
- `accruals` — начисления
- `payments` — платежи
- `expenses` — расходы
- `meters` — счётчики
- `reporting` — отчёты
- `administration` — auth

---

### Repository Pattern

**Интерфейс** (domain layer):
```python
class ILandPlotRepository(IRepository[LandPlot], ABC):
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> LandPlot | None: ...
    async def get_all(self, cooperative_id: UUID) -> list[LandPlot]: ...
    async def add(self, entity: LandPlot) -> LandPlot: ...
```

**Реализация** (infrastructure layer):
```python
class LandPlotRepository(ILandPlotRepository):
    def __init__(self, session: AsyncSession): ...
    
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> LandPlot | None:
        query = select(LandPlotModel).where(...)
        result = await self.session.execute(query)
        return model.to_domain() if model else None
```

---

### Dependency Injection

**Централизованный DI** (`modules/deps.py`):
```python
def get_land_plot_repository(db: AsyncSession = Depends(get_db)):
    from app.modules.land_management.infrastructure.repositories import LandPlotRepository
    return LandPlotRepository(db)

def get_create_land_plot_use_case(
    land_plot_repo=Depends(get_land_plot_repository),
    ownership_repo=Depends(get_plot_ownership_repository),
    event_dispatcher=Depends(get_event_dispatcher),
):
    from app.modules.land_management.application.use_cases import CreateLandPlotUseCase
    return CreateLandPlotUseCase(land_plot_repo, ownership_repo, event_dispatcher)
```

**Использование в API**:
```python
@router.post("/")
async def create_land_plot(
    data: LandPlotCreate,
    use_case: CreateLandPlotUseCase = Depends(get_create_land_plot_use_case),
) -> LandPlotWithOwners:
    return await use_case.execute(data)
```

---

### Domain Events

**Событие** (domain layer):
```python
@dataclass
class LandPlotCreated(DomainEvent):
    land_plot_id: UUID
    cooperative_id: UUID
    plot_number: str
    area_sqm: float
```

**Публикация** (use case):
```python
class CreateLandPlotUseCase:
    async def execute(self, data: LandPlotCreate) -> LandPlot:
        created_plot = await self.land_plot_repo.add(entity)
        
        # Создаём FinancialSubject
        await self.fs_use_case.execute(...)
        
        # Публикуем событие
        self.event_dispatcher.dispatch(LandPlotCreated(...))
        
        return created_plot
```

---

## 🎨 Frontend Patterns (Vue 3)

### Composition API

**Store** (Pinia):
```typescript
export const useLandPlotsStore = defineStore('landPlots', {
  state: () => ({
    plots: [] as LandPlot[],
    loading: false,
  }),
  
  actions: {
    async fetchPlots(cooperativeId: UUID) {
      this.loading = true
      try {
        const response = await api.getLandPlots(cooperativeId)
        this.plots = response.data
      } finally {
        this.loading = false
      }
    }
  }
})
```

**Component**:
```vue
<script setup lang="ts">
const landPlots = useLandPlotsStore()
const { cooperativeId } = useAuthStore()

onMounted(() => {
  landPlots.fetchPlots(cooperativeId)
})
</script>

<template>
  <div v-if="landPlots.loading">Загрузка...</div>
  <div v-else>
    <LandPlotCard v-for="plot in landPlots.plots" :key="plot.id" :plot="plot" />
  </div>
</template>
```

---

### Component Architecture

**Слои**:
```
src/
├── components/         # Переиспользуемые UI компоненты
│   ├── common/        # Кнопки, инпуты, модалки
│   └── land-plots/    # Специфичные для домена
├── views/             # Страницы (route components)
├── stores/            # Pinia stores
├── router/            # Vue Router config
└── api/               # API client
```

---

## 📊 Database Patterns

### Multitenancy (Изоляция СТ)

**Стратегия**: Database-level isolation (cooperative_id)

**Реализация**:
```python
class LandPlotModel(Base):
    __tablename__ = "land_plots"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    cooperative_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cooperatives.id"), nullable=False, index=True
    )
    plot_number: Mapped[str] = mapped_column(String(50))
    # ...

# Все запросы фильтруются по cooperative_id
query = select(LandPlotModel).where(
    LandPlotModel.cooperative_id == cooperative_id
)
```

---

### Historization (Аудит изменений)

**Паттерн**: Temporal tables (history tables)

**Пример**:
```python
class PlotOwnershipModel(Base):
    __tablename__ = "plot_ownerships"

class PlotOwnershipHistoryModel(Base):
    __tablename__ = "plot_ownerships_history"
    
    entity_id: Mapped[uuid.UUID]  # Ссылка на оригинальную запись
    changed_at: Mapped[datetime]
    operation: Mapped[str]  # INSERT, UPDATE, DELETE
    # ... копии всех полей ...
```

**Триггеры**: SQLAlchemy event listeners

---

## 🔐 Security Patterns

### JWT Authentication

**Flow**:
```
1. Login → POST /api/v1/auth/login
2. Server → JWT token (exp: 30 min)
3. Client → Store in localStorage
4. Requests → Authorization: Bearer <token>
5. Server → Validate + decode
```

**Token Payload**:
```python
{
    "sub": "username",
    "role": "treasurer",
    "cooperative_id": "uuid",
    "exp": 1234567890
}
```

---

### Role-Based Access Control (RBAC)

**Роли**:
- `admin` — полный доступ
- `chairman` — просмотр + начисления
- `treasurer` — финансы

**Реализация**:
```python
@router.post("/")
async def create_land_plot(
    current_user: Annotated[AppUser, Depends(require_role(["admin", "treasurer"]))],
    ...
):
    # Только admin и treasurer могут создавать участки
```

---

## 📡 API Design

### RESTful Convention

```
GET    /api/v1/land-plots          # Список
GET    /api/v1/land-plots/{id}     # Получить
POST   /api/v1/land-plots          # Создать
PATCH  /api/v1/land-plots/{id}     # Обновить
DELETE /api/v1/land-plots/{id}     # Удалить
```

### Response Format

**Success**:
```json
{
    "id": "uuid",
    "cooperative_id": "uuid",
    "plot_number": "123",
    "area_sqm": "600.00",
    "status": "active"
}
```

**Error**:
```json
{
    "detail": "Участок не найден",
    "status_code": 404
}
```

---

## 🔗 Связанные документы

- **Project Brief**: [`projectbrief.md`](projectbrief.md)
- **Architecture Docs**: [`../docs/architecture/`](../docs/architecture/)
- **Data Model**: [`../docs/data-model/`](../docs/data-model/)

---

*Последнее обновление: 28 февраля 2026*
