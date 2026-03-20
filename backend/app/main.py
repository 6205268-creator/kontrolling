from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.session import async_session_maker
from app.modules.accruals.api.contribution_types import router as contribution_types_router
from app.modules.accruals.api.routes import router as accruals_router
from app.modules.administration.api.routes import router as administration_router

# Modular API routers (Clean Architecture)
from app.modules.cooperative_core.api.routes import router as cooperative_core_router
from app.modules.expenses.api.routes import router as expenses_router
from app.modules.financial_core.api.routes import router as financial_core_router
from app.modules.financial_core.infrastructure.event_handlers import setup_event_handlers
from app.modules.financial_core.infrastructure.repositories import FinancialSubjectRepository
from app.modules.land_management.api.owners_routes import router as owners_router
from app.modules.land_management.api.routes import router as land_management_router
from app.modules.meters.api.routes import router as meters_router
from app.modules.payment_distribution.api.routes import router as payment_distribution_router
from app.modules.payment_distribution.infrastructure.event_handlers import (
    setup_payment_distribution_handlers,
)
from app.modules.payments.api.routes import router as payments_router
from app.modules.reporting.api.routes import router as reporting_router
from app.modules.shared.kernel.events import EventDispatcher

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="""
## Controlling API — Система учёта хозяйственной деятельности садоводческих товариществ (СТ)

### Основные возможности

- **Аутентификация и авторизация** — JWT токены, роли пользователей (admin, chairman, treasurer)
- **Управление СТ** — создание и редактирование садоводческих товариществ
- **Владельцы** — учёт физических и юридических лиц
- **Участки** — кадастровый учёт земельных участков с правами собственности (долевое владение)
- **Финансовые субъекты** — централизованное управление финансовыми обязательствами
- **Начисления** — создание и учёт членских и целевых взносов
- **Платежи** — регистрация поступлений от владельцев
- **Расходы** — учёт расходов товарищества по категориям
- **Счётчики** — приборы учёта (вода, электричество) с историей показаний
- **Отчёты** — анализ должников и движение денежных средств

### Ролевая модель

- **admin** — полный доступ ко всем функциям и данным всех СТ
- **chairman** — просмотр данных своего СТ, создание начислений
- **treasurer** — полный доступ к финансовым операциям своего СТ (начисления, платежи, расходы)

### Безопасность

Все защищённые эндпоинты требуют JWT токен в заголовке `Authorization: Bearer <token>`.
Получение токена: `POST /api/auth/login`.
""",
    docs_url="/docs",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Аутентификация пользователей: получение JWT токена и информация о текущем пользователе.",
        },
        {
            "name": "cooperatives",
            "description": "Управление садоводческими товариществами (СТ): создание, редактирование, просмотр списка.",
        },
        {
            "name": "owners",
            "description": "Управление владельцами: физические и юридические лица, поиск по имени и УНП.",
        },
        {
            "name": "land-plots",
            "description": "Управление земельными участками: создание, редактирование, права собственности (долевое владение).",
        },
        {
            "name": "financial-subjects",
            "description": "Финансовые субъекты: централизованные объекты финансовой ответственности (участки, счётчики).",
        },
        {
            "name": "contribution-types",
            "description": "Справочник видов взносов: членские, целевые и другие типы взносов.",
        },
        {
            "name": "accruals",
            "description": "Начисления: создание, применение и отмена взносов для финансовых субъектов.",
        },
        {
            "name": "payments",
            "description": "Платежи: регистрация поступлений от владельцев, отмена платежей.",
        },
        {
            "name": "expenses",
            "description": "Расходы товарищества: учёт затрат по категориям, подтверждение и отмена.",
        },
        {
            "name": "meters",
            "description": "Приборы учёта: счётчики воды и электричества, история показаний.",
        },
        {
            "name": "reports",
            "description": "Отчёты: анализ должников и движение денежных средств (cash flow).",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup event handlers for domain events (logging, auto-creation of FinancialSubjects)
_event_dispatcher = EventDispatcher()
setup_event_handlers(_event_dispatcher, async_session_maker, FinancialSubjectRepository)
setup_payment_distribution_handlers(_event_dispatcher, async_session_maker)

# API routers
app.include_router(cooperative_core_router, prefix="/api/cooperatives", tags=["cooperatives"])
app.include_router(owners_router, prefix="/api/owners", tags=["owners"])
app.include_router(land_management_router, prefix="/api/land-plots", tags=["land-plots"])
app.include_router(
    financial_core_router, prefix="/api/financial-subjects", tags=["financial-subjects"]
)
app.include_router(accruals_router, prefix="/api/accruals", tags=["accruals"])
app.include_router(
    contribution_types_router, prefix="/api/contribution-types", tags=["contribution-types"]
)
app.include_router(payments_router, prefix="/api/payments", tags=["payments"])
app.include_router(
    payment_distribution_router,
    prefix="/api/payment-distribution",
    tags=["payment-distribution"],
)
app.include_router(meters_router, prefix="/api/meters", tags=["meters"])
app.include_router(expenses_router, prefix="/api/expenses", tags=["expenses"])
app.include_router(reporting_router, prefix="/api/reports", tags=["reports"])
app.include_router(administration_router, prefix="/api/auth", tags=["auth"])


def _get_error_detail(exc: Exception) -> str:
    """Формирует сообщение об ошибке для ответа 500 (без утечки внутренних деталей в prod)."""
    msg = str(exc).lower()
    if (
        "connection" in msg
        or "refused" in msg
        or "timeout" in msg
        or "5432" in msg
        or "asyncpg" in msg
    ):
        return "Нет связи с базой данных. Проверьте, что PostgreSQL запущен и в backend/.env задан верный DATABASE_URL."
    return "Внутренняя ошибка сервера. Проверьте консоль бэкенда."


@app.exception_handler(Exception)
def unhandled_exception_handler(_request: object, exc: Exception) -> JSONResponse:
    """Обработка необработанных исключений — возвращаем 500 с понятным текстом."""
    detail = _get_error_detail(exc)
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
