from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.accruals import router as accruals_router
from app.db.history_events import register_history_events
from app.api.v1.auth import router as auth_router
from app.api.v1.cooperatives import router as cooperatives_router
from app.api.v1.contribution_types import router as contribution_types_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.financial_subjects import router as financial_subjects_router
from app.api.v1.land_plots import router as land_plots_router
from app.api.v1.meters import router as meters_router
from app.api.v1.owners import router as owners_router
from app.api.v1.payments import router as payments_router
from app.api.v1.reports import router as reports_router
from app.config import settings

register_history_events()

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
Получение токена: `POST /api/v1/auth/login`.
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

# API v1 routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(cooperatives_router, prefix="/api/v1/cooperatives", tags=["cooperatives"])
app.include_router(owners_router, prefix="/api/v1/owners", tags=["owners"])
app.include_router(land_plots_router, prefix="/api/v1/land-plots", tags=["land-plots"])
app.include_router(financial_subjects_router, prefix="/api/v1/financial-subjects", tags=["financial-subjects"])
app.include_router(contribution_types_router, prefix="/api/v1/contribution-types", tags=["contribution-types"])
app.include_router(accruals_router, prefix="/api/v1/accruals", tags=["accruals"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(expenses_router, prefix="/api/v1/expenses", tags=["expenses"])
app.include_router(meters_router, prefix="/api/v1/meters", tags=["meters"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
