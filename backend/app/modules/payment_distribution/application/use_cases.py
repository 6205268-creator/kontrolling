"""
Use Cases for Payment Distribution module.

Бизнес-операции модуля распределения платежей.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from ..domain.entities import (
    Member,
    PaymentDistributionRule,
    PersonalAccount,
)
from ..domain.events import (
    MemberCreated,
    PersonalAccountOpened,
)
from ..domain.repositories import (
    IDistributionRuleRepository,
    IMemberRepository,
    IPaymentDistributionRepository,
    IPersonalAccountRepository,
)
from .dtos import (
    CancelPaymentResult,
    DistributePaymentResult,
    DistributionRuleCreateDTO,
    MemberCreateDTO,
    MemberResponseDTO,
    PaymentCreateDTO,
    PaymentDistributionRuleResponseDTO,
    PaymentResponseDTO,
)


class CreateMemberUseCase:
    """Создание члена СТ и открытие лицевого счёта."""

    def __init__(
        self,
        member_repository: IMemberRepository,
        account_repository: IPersonalAccountRepository,
        event_dispatcher: "EventDispatcher",
    ):
        self.member_repository = member_repository
        self.account_repository = account_repository
        self.event_dispatcher = event_dispatcher

    async def execute(self, dto: MemberCreateDTO) -> MemberResponseDTO:
        # Проверка: не является ли Owner уже членом этого СТ
        existing = await self.member_repository.get_by_owner_and_cooperative(
            dto.owner_id, dto.cooperative_id
        )
        if existing:
            raise ValueError("Owner уже является членом этого СТ")

        # Создание Member
        member = Member(
            id=uuid4(),
            owner_id=dto.owner_id,
            cooperative_id=dto.cooperative_id,
            status="active",
            joined_date=dto.joined_date,
        )
        member = await self.member_repository.create(member)

        # Создание PersonalAccount
        account_number = await self._generate_account_number(member.cooperative_id)
        account = PersonalAccount(
            id=uuid4(),
            member_id=member.id,
            cooperative_id=member.cooperative_id,
            account_number=account_number,
            balance=Decimal("0.00"),
            status="active",
            opened_at=datetime.utcnow(),
        )
        account = await self.account_repository.create(account)

        # Доменные события
        await self.event_dispatcher.dispatch(
            MemberCreated(
                member_id=member.id,
                owner_id=member.owner_id,
                cooperative_id=member.cooperative_id,
            )
        )
        await self.event_dispatcher.dispatch(
            PersonalAccountOpened(
                account_id=account.id,
                member_id=account.member_id,
                cooperative_id=account.cooperative_id,
                account_number=account.account_number,
            )
        )

        return MemberResponseDTO(
            id=member.id,
            owner_id=member.owner_id,
            cooperative_id=member.cooperative_id,
            status=member.status,
            joined_date=member.joined_date,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )

    async def _generate_account_number(self, cooperative_id: UUID) -> str:
        """Генерация уникального номера счёта."""
        # Формат: LS-YYYY-#####
        year = datetime.utcnow().year
        accounts = await self.account_repository.get_by_cooperative(cooperative_id)
        next_num = len(accounts) + 1
        return f"LS-{year}-{next_num:05d}"


class ReceivePaymentUseCase:
    """Регистрация платежа и зачисление на лицевой счёт."""

    def __init__(
        self,
        account_repository: IPersonalAccountRepository,
        payment_repository: "IPaymentRepository",
        distribute_use_case: "DistributePaymentUseCase",
        event_dispatcher: "EventDispatcher",
    ):
        self.account_repository = account_repository
        self.payment_repository = payment_repository
        self.distribute_use_case = distribute_use_case
        self.event_dispatcher = event_dispatcher

    async def execute(self, dto: PaymentCreateDTO) -> PaymentResponseDTO:
        # Найти Member по owner_id
        # (упрощённо: предполагаем, что Member уже существует)
        # В реальной реализации нужно загрузить Member через repository

        # Найти PersonalAccount владельца
        # account = await self.account_repository.get_by_member(member_id)
        # if not account:
        #     raise ValueError("PersonalAccount не найден")

        # Создать Payment
        # payment = await self.payment_repository.create(...)

        # Создать PersonalAccountTransaction (приход)
        # transaction = PersonalAccountTransaction(...)
        # await self.account_repository.add_transaction(transaction)

        # Обновить баланс счёта
        # account.balance += dto.total_amount
        # await self.account_repository.update(account)

        # Автоматически запустить распределение
        # result = await self.distribute_use_case.execute(payment.id)

        # Доменное событие
        # await self.event_dispatcher.dispatch(PaymentReceived(...))

        # Вернуть ответ
        # return PaymentResponseDTO(...)

        # TODO: Реализовать после создания PaymentRepository
        raise NotImplementedError("Требуется реализация PaymentRepository")


class DistributePaymentUseCase:
    """Распределение платежа по задолженностям согласно приоритетам."""

    def __init__(
        self,
        payment_repository: "IPaymentRepository",
        account_repository: IPersonalAccountRepository,
        distribution_repository: IPaymentDistributionRepository,
        rule_repository: IDistributionRuleRepository,
        accrual_repository: "IAccrualRepository",
        financial_subject_repository: "IFinancialSubjectRepository",
        event_dispatcher: "EventDispatcher",
    ):
        self.payment_repository = payment_repository
        self.account_repository = account_repository
        self.distribution_repository = distribution_repository
        self.rule_repository = rule_repository
        self.accrual_repository = accrual_repository
        self.financial_subject_repository = financial_subject_repository
        self.event_dispatcher = event_dispatcher

    async def execute(self, payment_id: UUID) -> DistributePaymentResult:
        # 1. Загрузить платёж
        # payment = await self.payment_repository.get_by_id(payment_id)
        # if not payment:
        #     raise ValueError("Платёж не найден")

        # 2. Загрузить правила распределения для cooperative
        # rules = await self.rule_repository.get_by_cooperative(
        #     payment.cooperative_id, is_active=True
        # )
        # rules.sort(key=lambda r: r.priority)

        # 3. Загрузить непогашенные Accrual владельца
        # accruals = await self.accrual_repository.get_unpaid_by_member(member_id)

        # 4. Распределить по приоритетам
        # remaining_amount = payment.total_amount
        # distributions = []

        # for rule in rules:
        #     if remaining_amount <= 0:
        #         break

        #     # Найти Accrual соответствующего типа
        #     accrual = self._find_accrual_by_rule(accruals, rule)
        #     if not accrual:
        #         continue

        #     # Вычислить сумму распределения
        #     debt_remaining = accrual.amount - accrual.paid_amount
        #     distribute_amount = min(remaining_amount, debt_remaining)

        #     # Создать PaymentDistribution
        #     distribution = PaymentDistribution(
        #         id=uuid4(),
        #         payment_id=payment.id,
        #         financial_subject_id=accrual.financial_subject_id,
        #         distribution_number=await self._generate_distribution_number(),
        #         distributed_at=datetime.utcnow(),
        #         amount=distribute_amount,
        #         priority=rule.priority,
        #         status="applied",
        #     )
        #     distribution = await self.distribution_repository.create(distribution)
        #     distributions.append(distribution)

        #     # Создать PersonalAccountTransaction (расход)
        #     transaction = PersonalAccountTransaction(
        #         id=uuid4(),
        #         account_id=account.id,
        #         payment_id=payment.id,
        #         distribution_id=distribution.id,
        #         transaction_number=await self._generate_transaction_number(),
        #         transaction_date=datetime.utcnow(),
        #         amount=-distribute_amount,
        #         type="distribution",
        #     )
        #     await self.account_repository.add_transaction(transaction)

        #     # Обновить paid_amount у Accrual
        #     accrual.paid_amount += distribute_amount
        #     if accrual.paid_amount >= accrual.amount:
        #         accrual.status = "paid"
        #     await self.accrual_repository.update(accrual)

        #     remaining_amount -= distribute_amount

        # 5. Обновить баланс счёта
        # account.balance -= (payment.total_amount - remaining_amount)
        # await self.account_repository.update(account)

        # 6. Обновить статус платежа
        # if remaining_amount <= 0:
        #     payment.status = "distributed"
        # else:
        #     payment.status = "partial"
        # await self.payment_repository.update(payment)

        # 7. Доменное событие
        # await self.event_dispatcher.dispatch(PaymentDistributed(...))

        # return DistributePaymentResult(...)

        # TODO: Реализовать после создания репозиториев
        raise NotImplementedError("Требуется реализация репозиториев")

    def _find_accrual_by_rule(
        self, accruals: List, rule: PaymentDistributionRule
    ) -> Optional[object]:
        """Найти Accrual по правилу распределения."""
        # TODO: Реализовать логику поиска
        return None

    async def _generate_distribution_number(self) -> str:
        """Генерация номера распределения."""
        # Формат: РП-YYYY-#####-##
        year = datetime.utcnow().year
        return f"РП-{year}-00001-01"  # TODO: Реальная генерация

    async def _generate_transaction_number(self) -> str:
        """Генерация номера транзакции."""
        # Формат: ТС-YYYY-#####
        year = datetime.utcnow().year
        return f"ТС-{year}-00001"  # TODO: Реальная генерация


class CancelPaymentUseCase:
    """Отмена платежа с возвратом на счёт."""

    def __init__(
        self,
        payment_repository: "IPaymentRepository",
        distribution_repository: IPaymentDistributionRepository,
        account_repository: IPersonalAccountRepository,
        accrual_repository: "IAccrualRepository",
        event_dispatcher: "EventDispatcher",
    ):
        self.payment_repository = payment_repository
        self.distribution_repository = distribution_repository
        self.account_repository = account_repository
        self.accrual_repository = accrual_repository
        self.event_dispatcher = event_dispatcher

    async def execute(self, payment_id: UUID, reason: str) -> CancelPaymentResult:
        # 1. Загрузить платёж
        # 2. Проверить, что не был ранее отменён
        # 3. Отменить все PaymentDistribution
        # 4. Восстановить paid_amount у Accrual
        # 5. Создать PersonalAccountTransaction (возврат)
        # 6. Обновить баланс счёта
        # 7. Обновить статус платежа
        # 8. Доменное событие PaymentCancelled

        # TODO: Реализовать после создания репозиториев
        raise NotImplementedError("Требуется реализация репозиториев")


class CreateDistributionRuleUseCase:
    """Создание правила распределения платежей."""

    def __init__(
        self,
        rule_repository: IDistributionRuleRepository,
        event_dispatcher: "EventDispatcher",
    ):
        self.rule_repository = rule_repository
        self.event_dispatcher = event_dispatcher

    async def execute(self, dto: DistributionRuleCreateDTO) -> PaymentDistributionRuleResponseDTO:
        # 1. Проверить уникальность priority для cooperative
        # existing_rules = await self.rule_repository.get_by_cooperative(dto.cooperative_id)
        # if any(r.priority == dto.priority for r in existing_rules):
        #     raise ValueError("Правило с таким приоритетом уже существует")

        # 2. Проверить валидность rule_type
        # if dto.rule_type in ["membership", "target", "additional"]:
        #     if not dto.contribution_type_id:
        #         raise ValueError("Требуется contribution_type_id для взносов")
        # elif dto.rule_type in ["meter_water", "meter_electricity"]:
        #     if not dto.meter_type:
        #         raise ValueError("Требуется meter_type для счётчиков")

        # 3. Создать правило
        # rule = PaymentDistributionRule(
        #     id=uuid4(),
        #     settings_module_id=...,  # TODO: Загрузить модуль настроек
        #     rule_type=dto.rule_type,
        #     priority=dto.priority,
        #     contribution_type_id=dto.contribution_type_id,
        #     meter_type=dto.meter_type,
        #     is_active=True,
        # )
        # rule = await self.rule_repository.create(rule)

        # 4. Доменное событие
        # await self.event_dispatcher.dispatch(DistributionRuleCreated(...))

        # 5. Вернуть ответ
        # return PaymentDistributionRuleResponseDTO(...)

        # TODO: Реализовать после создания репозиториев
        raise NotImplementedError("Требуется реализация репозиториев")


# =============================================================================
# Event Dispatcher (заглушка для примера)
# =============================================================================


class EventDispatcher:
    """Диспетчер доменных событий."""

    async def dispatch(self, event):
        """Отправить событие."""
        # TODO: Реализовать отправку событий (логирование, уведомления...)
        pass


# =============================================================================
# Repository Stubs (заглушки для примера)
# =============================================================================


class IPaymentRepository:
    """Репозиторий для платежей (заглушка)."""

    pass


class IAccrualRepository:
    """Репозиторий для начислений (заглушка)."""

    pass


class IFinancialSubjectRepository:
    """Репозиторий для финансовых субъектов (заглушка)."""

    pass
