"""Регистрация SQLAlchemy event listeners для записи истории изменений.

При insert/update/delete сущностей PlotOwnership, Accrual, Payment, Expense
в ту же транзакцию добавляется запись в соответствующую *_history таблицу.
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import event, insert
from sqlalchemy.orm import Mapper


def _get_history_config():
    """Lazy import of models to avoid circular dependencies."""
    from app.modules.land_management.infrastructure.models import (
        PlotOwnershipModel as PlotOwnership,
        PlotOwnershipHistoryModel as PlotOwnershipHistory,
    )
    from app.modules.accruals.infrastructure.models import (
        AccrualModel as Accrual,
        AccrualHistoryModel as AccrualHistory,
    )
    from app.modules.payments.infrastructure.models import (
        PaymentModel as Payment,
        PaymentHistoryModel as PaymentHistory,
    )
    from app.modules.expenses.infrastructure.models import (
        ExpenseModel as Expense,
        ExpenseHistoryModel as ExpenseHistory,
    )
    
    return [
        (
            PlotOwnership,
            PlotOwnershipHistory,
            [
                "land_plot_id",
                "owner_id",
                "share_numerator",
                "share_denominator",
                "is_primary",
                "valid_from",
                "valid_to",
                "created_at",
                "updated_at",
            ],
        ),
        (
            Accrual,
            AccrualHistory,
            [
                "financial_subject_id",
                "contribution_type_id",
                "amount",
                "accrual_date",
                "period_start",
                "period_end",
                "status",
                "created_at",
                "updated_at",
            ],
        ),
        (
            Payment,
            PaymentHistory,
            [
                "financial_subject_id",
                "payer_owner_id",
                "amount",
                "payment_date",
                "document_number",
                "description",
                "status",
                "created_at",
                "updated_at",
            ],
        ),
        (
            Expense,
            ExpenseHistory,
            [
                "cooperative_id",
                "category_id",
                "amount",
                "expense_date",
                "document_number",
                "description",
                "status",
                "created_at",
                "updated_at",
            ],
        ),
    ]


def _snapshot_row(target: object, snapshot_columns: list[str]) -> dict:
    """Собрать снимок полей сущности в словарь."""
    return {col: getattr(target, col, None) for col in snapshot_columns}


def _make_history_listener(history_table: type, snapshot_columns: list[str], operation: str):
    def listener(mapper: Mapper, connection, target: object) -> None:
        now = datetime.now(UTC)
        row = {
            "id": uuid4(),
            "entity_id": target.id,
            "changed_at": now,
            "operation": operation,
            **_snapshot_row(target, snapshot_columns),
        }
        connection.execute(insert(history_table.__table__).values(**row))

    return listener


def register_history_events() -> None:
    """Подключить after_insert/after_update/after_delete для всех аудируемых моделей."""
    for entity_class, history_class, snapshot_columns in _get_history_config():
        event.listens_for(entity_class, "after_insert")(
            _make_history_listener(history_class, snapshot_columns, "insert"),
        )
        event.listens_for(entity_class, "after_update")(
            _make_history_listener(history_class, snapshot_columns, "update"),
        )
        event.listens_for(entity_class, "after_delete")(
            _make_history_listener(history_class, snapshot_columns, "delete"),
        )
