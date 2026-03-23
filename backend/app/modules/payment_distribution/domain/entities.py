"""Payment Distribution domain entities.

Pure Python - no framework dependencies (FastAPI, SQLAlchemy, Pydantic).

This module implements payment distribution according to ADR 0003:
- Member: thin technical entity linking Owner to Cooperative via PersonalAccount
- PersonalAccount: member's "wallet" for payments
- PersonalAccountTransaction: credit/debit transactions
- PaymentDistribution: allocation of payment to specific debts
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.shared.kernel.money import Money


@dataclass
class Member:
    """Член СТ — техническая сущность связи Owner ↔ Cooperative.

    Создаётся автоматически при первом PlotOwnership.is_primary = true
    для данного Owner в данном Cooperative.

    Атрибуты:
        id: Уникальный идентификатор.
        owner_id: ID владельца (физическое или юридическое лицо).
        cooperative_id: ID садоводческого товарищества.
        personal_account_id: ID лицевого счёта члена.
        status: Статус (active, closed).
        joined_at: Дата вступления в члены СТ.
        created_at: Дата создания записи.
    """

    owner_id: UUID
    cooperative_id: UUID
    personal_account_id: UUID | None = None
    status: str = "active"  # active, closed
    joined_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime | None = None
    id: UUID | None = None

    def close(self, closed_at: datetime) -> None:
        """Закрыть членство в СТ.

        Args:
            closed_at: Дата закрытия.
        """
        self.status = "closed"
        self.closed_at = closed_at


@dataclass
class PersonalAccount:
    """Лицевой счёт члена СТ.

    «Кошелёк» для зачисления платежей и распределения по долгам.
    Баланс может быть положительным (аванс) или нулевым.

    Атрибуты:
        id: Уникальный идентификатор.
        member_id: ID члена СТ.
        cooperative_id: ID СТ (для индексации).
        account_number: Человекочитаемый номер счёта.
        balance: Текущий баланс счёта.
        status: Статус (active, closed).
        opened_at: Дата открытия счёта.
        closed_at: Дата закрытия (если закрыт).
        created_at: Дата создания записи.
    """

    member_id: UUID
    cooperative_id: UUID
    account_number: str
    balance: Money
    status: str = "active"  # active, closed
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime | None = None
    id: UUID | None = None

    def credit(self, amount: Money) -> None:
        """Зачислить сумму на счёт.

        Args:
            amount: Сумма зачисления (положительная).
        """
        if not amount.is_positive:
            raise ValueError("Credit amount must be positive")
        self.balance = Money(self.balance.amount + amount.amount)

    def debit(self, amount: Money) -> None:
        """Списать сумму со счёта.

        Args:
            amount: Сумма списания (положительная).

        Raises:
            ValueError: Если сумма недостаточна.
        """
        if not amount.is_positive:
            raise ValueError("Debit amount must be positive")
        if amount.amount > self.balance.amount:
            raise ValueError("Insufficient balance")
        self.balance = Money(self.balance.amount - amount.amount)

    def close(self, closed_at: datetime) -> None:
        """Закрыть лицевой счёт.

        Args:
            closed_at: Дата закрытия.

        Raises:
            ValueError: Если баланс не нулевой.
        """
        if not self.balance.is_zero:
            raise ValueError("Cannot close account with non-zero balance")
        self.status = "closed"
        self.closed_at = closed_at


@dataclass
class PersonalAccountTransaction:
    """Транзакция по лицевому счёту.

    Запись о зачислении (credit) или списании (debit) средств.

    Атрибуты:
        id: Уникальный идентификатор.
        account_id: ID лицевого счёта.
        payment_id: ID платежа (если зачисление от платежа).
        distribution_id: ID распределения (если списание в счёт долга).
        transaction_number: Уникальный номер транзакции.
        transaction_date: Дата и время транзакции.
        amount: Сумма транзакции (всегда положительная).
        type: Тип транзакции (credit, debit).
        description: Описание (опционально).
        created_at: Дата создания записи.
    """

    account_id: UUID
    transaction_number: str
    transaction_date: datetime
    amount: Money
    type: str  # credit, debit
    payment_id: UUID | None = None
    distribution_id: UUID | None = None
    description: str | None = None
    created_at: datetime | None = None
    id: UUID | None = None


@dataclass
class PaymentDistribution:
    """Распределение платежа по начислению.

    Запись «из этого платежа X BYN пошли на погашение начисления Y
    через FinancialSubject Z».

    Атрибуты:
        id: Уникальный идентификатор.
        payment_id: ID исходного платежа.
        financial_subject_id: ID финансового субъекта.
        accrual_id: ID конкретного начисления (если известно).
        distribution_number: Уникальный номер распределения.
        distributed_at: Дата распределения.
        amount: Сумма распределения.
        priority: Приоритет по правилу распределения.
        status: Статус (applied, reversed).
        created_at: Дата создания записи.
    """

    payment_id: UUID
    financial_subject_id: UUID
    distribution_number: str
    distributed_at: datetime
    amount: Money
    priority: int
    status: str = "applied"  # applied, reversed
    accrual_id: UUID | None = None
    created_at: datetime | None = None
    id: UUID | None = None

    def reverse(self, reversed_at: datetime) -> None:
        """Отменить распределение (при отмене платежа).

        Args:
            reversed_at: Дата отмены.

        Raises:
            ValueError: Если уже отменено.
        """
        if self.status == "reversed":
            raise ValueError("Distribution already reversed")
        self.status = "reversed"
