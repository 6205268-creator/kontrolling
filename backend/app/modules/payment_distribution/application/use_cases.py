"""
Use Cases for Payment Distribution module.

Бизнес-операции модуля распределения платежей.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from ..domain.entities import (
    Member,
    PaymentDistributionRule,
    PersonalAccount,
    PersonalAccountTransaction,
    SettingsModule,
)
from ..domain.entities import (
    PaymentDistribution as PaymentDistributionEntity,
)
from ..domain.events import (
    DistributionRuleCreated,
    MemberCreated,
    PaymentCancelled,
    PaymentDistributed,
    PaymentReceived,
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
    PaymentDistributionResponseDTO,
    PaymentDistributionRuleResponseDTO,
    PaymentResponseDTO,
)

if TYPE_CHECKING:
    from app.modules.accruals.domain.entities import Accrual
    from app.modules.payments.domain.entities import Payment as PaymentEntity


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
        member_repository: IMemberRepository,
        account_repository: IPersonalAccountRepository,
        payment_repository: "IPaymentRepository",
        distribute_use_case: "DistributePaymentUseCase",
        event_dispatcher: "EventDispatcher",
    ):
        self.member_repository = member_repository
        self.account_repository = account_repository
        self.payment_repository = payment_repository
        self.distribute_use_case = distribute_use_case
        self.event_dispatcher = event_dispatcher

    async def execute(self, dto: PaymentCreateDTO) -> PaymentResponseDTO:
        # 1. Найти Member по owner_id
        member = await self._get_member_by_owner(dto.from_owner_id)
        if not member:
            raise ValueError("Member не найден для этого владельца")

        # 2. Найти PersonalAccount
        account = await self.account_repository.get_by_member(member.id)
        if not account:
            raise ValueError("PersonalAccount не найден")

        # 3. Создать Payment
        payment = await self.payment_repository.create(
            from_owner_id=dto.from_owner_id,
            total_amount=dto.total_amount,
            payment_date=dto.payment_date,
            document_number=dto.document_number,
            description=dto.description,
        )

        # 4. Создать PersonalAccountTransaction (приход)
        transaction = PersonalAccountTransaction(
            id=uuid4(),
            account_id=account.id,
            payment_id=payment.id,
            distribution_id=None,
            transaction_number=await self._generate_transaction_number(),
            transaction_date=datetime.utcnow(),
            amount=dto.total_amount,
            type="payment_received",
            description=dto.description or f"Платёж {payment.id}",
        )
        await self.account_repository.add_transaction(transaction)

        # 5. Обновить баланс счёта
        account.balance += dto.total_amount
        await self.account_repository.update(account)

        # 6. Автоматически запустить распределение
        await self.distribute_use_case.execute(payment.id)

        # 7. Доменное событие
        await self.event_dispatcher.dispatch(
            PaymentReceived(
                payment_id=payment.id,
                owner_id=dto.from_owner_id,
                account_id=account.id,
                amount=dto.total_amount,
            )
        )

        # 8. Вернуть ответ
        return await self._get_payment_response(payment.id)

    async def _get_member_by_owner(self, owner_id: UUID) -> Optional[Member]:
        """Получить Member по owner_id (упрощённо — первый активный)."""
        # В полной реализации нужно передавать cooperative_id
        # Здесь заглушка — нужно получить из контекста
        raise NotImplementedError("Требуется cooperative_id для поиска Member")

    async def _generate_transaction_number(self) -> str:
        """Генерация номера транзакции: ТС-YYYY-#####."""
        year = datetime.utcnow().year
        # В реальности нужно получать следующий номер из БД
        return f"ТС-{year}-00001"

    async def _get_payment_response(self, payment_id: UUID) -> PaymentResponseDTO:
        """Получить ответ платежа с распределениями."""
        payment = await self.payment_repository.get_by_id(payment_id)
        distributions = await self.payment_repository.get_distributions(payment_id)

        return PaymentResponseDTO(
            id=payment.id,
            from_owner_id=payment.from_owner_id,
            total_amount=payment.total_amount,
            payment_date=payment.payment_date,
            document_number=payment.document_number,
            description=payment.description,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            distributions=distributions,
        )


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
        member_repository: IMemberRepository,
        event_dispatcher: "EventDispatcher",
    ):
        self.payment_repository = payment_repository
        self.account_repository = account_repository
        self.distribution_repository = distribution_repository
        self.rule_repository = rule_repository
        self.accrual_repository = accrual_repository
        self.financial_subject_repository = financial_subject_repository
        self.member_repository = member_repository
        self.event_dispatcher = event_dispatcher

    async def execute(self, payment_id: UUID) -> DistributePaymentResult:
        # 1. Загрузить платёж
        payment = await self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Платёж не найден")

        if payment.status != "pending":
            raise ValueError(f"Платёж уже обработан: status={payment.status}")

        # 2. Найти Member по owner_id
        member = await self._get_member_by_owner(payment.from_owner_id)
        if not member:
            # Нет членства — не распределяем, оставляем на счёте
            return await self._complete_without_distribution(payment)

        # 3. Найти PersonalAccount
        account = await self.account_repository.get_by_member(member.id)
        if not account:
            raise ValueError("PersonalAccount не найден")

        # 4. Загрузить правила распределения для cooperative
        rules = await self.rule_repository.get_by_cooperative(member.cooperative_id, is_active=True)
        rules.sort(key=lambda r: r.priority)

        # 5. Загрузить непогашенные Accrual владельца
        accruals = await self.accrual_repository.get_unpaid_by_member(member.id)

        # 6. Распределить по приоритетам
        remaining_amount = payment.total_amount
        distributions: List[PaymentDistributionResponseDTO] = []

        for rule in rules:
            if remaining_amount <= Decimal("0"):
                break

            # Найти Accrual соответствующего типа
            accrual = self._find_accrual_by_rule(accruals, rule, member.cooperative_id)
            if not accrual:
                continue

            # Вычислить сумму распределения
            debt_remaining = accrual.amount - accrual.paid_amount
            if debt_remaining <= Decimal("0"):
                continue

            distribute_amount = min(remaining_amount, debt_remaining)

            # Создать PaymentDistribution
            distribution = PaymentDistributionEntity(
                id=uuid4(),
                payment_id=payment.id,
                financial_subject_id=accrual.financial_subject_id,
                distribution_number=await self._generate_distribution_number(),
                distributed_at=datetime.utcnow(),
                amount=distribute_amount,
                priority=rule.priority,
                status="applied",
            )
            await self.distribution_repository.create(distribution)

            # Создать PersonalAccountTransaction (расход)
            transaction = PersonalAccountTransaction(
                id=uuid4(),
                account_id=account.id,
                payment_id=payment.id,
                distribution_id=distribution.id,
                transaction_number=await self._generate_transaction_number(),
                transaction_date=datetime.utcnow(),
                amount=-distribute_amount,
                type="distribution",
                description=f"Распределение {distribution.id}",
            )
            await self.account_repository.add_transaction(transaction)

            # Обновить paid_amount у Accrual
            accrual.paid_amount += distribute_amount
            if accrual.paid_amount >= accrual.amount:
                accrual.status = "paid"
            await self.accrual_repository.update(accrual)

            # Добавить в результат
            distributions.append(
                PaymentDistributionResponseDTO(
                    id=distribution.id,
                    payment_id=distribution.payment_id,
                    financial_subject_id=distribution.financial_subject_id,
                    distribution_number=distribution.distribution_number,
                    distributed_at=distribution.distributed_at,
                    amount=distribution.amount,
                    priority=distribution.priority,
                    status=distribution.status,
                )
            )

            remaining_amount -= distribute_amount

        # 7. Обновить баланс счёта
        distributed_total = payment.total_amount - remaining_amount
        account.balance -= distributed_total
        await self.account_repository.update(account)

        # 8. Обновить статус платежа
        if remaining_amount <= Decimal("0"):
            payment.status = "distributed"
        else:
            payment.status = "partial"
        await self.payment_repository.update(payment)

        # 9. Доменное событие
        await self.event_dispatcher.dispatch(
            PaymentDistributed(
                payment_id=payment.id,
                distributions=[d.id for d in distributions],
                total_distributed=distributed_total,
                remaining_balance=remaining_amount,
            )
        )

        return DistributePaymentResult(
            payment_id=payment.id,
            distributions=distributions,
            total_distributed=distributed_total,
            remaining_on_account=remaining_amount,
            status=payment.status,
        )

    async def _get_member_by_owner(self, owner_id: UUID) -> Optional[Member]:
        """Получить Member по owner_id."""
        # В полной реализации нужно передавать cooperative_id
        raise NotImplementedError("Требуется cooperative_id для поиска Member")

    def _find_accrual_by_rule(
        self, accruals: List["Accrual"], rule: PaymentDistributionRule, cooperative_id: UUID
    ) -> Optional["Accrual"]:
        """Найти Accrual по правилу распределения."""
        for accrual in accruals:
            if accrual.status != "active":
                continue

            # Проверка по типу правила
            if (
                rule.rule_type == "membership"
                and accrual.contribution_type_id == rule.contribution_type_id
            ):
                return accrual
            elif (
                rule.rule_type == "target"
                and accrual.contribution_type_id == rule.contribution_type_id
            ):
                return accrual
            elif (
                rule.rule_type == "additional"
                and accrual.contribution_type_id == rule.contribution_type_id
            ):
                return accrual
            # Для счётчиков нужна отдельная логика
            # TODO: Добавить проверку для meter_water и meter_electricity

        return None

    async def _complete_without_distribution(
        self, payment: "PaymentEntity"
    ) -> DistributePaymentResult:
        """Завершить платёж без распределения (нет членства)."""
        payment.status = "distributed"
        await self.payment_repository.update(payment)

        return DistributePaymentResult(
            payment_id=payment.id,
            distributions=[],
            total_distributed=Decimal("0"),
            remaining_on_account=payment.total_amount,
            status="distributed",
        )

    async def _generate_distribution_number(self) -> str:
        """Генерация номера распределения: РП-YYYY-#####-##."""
        year = datetime.utcnow().year
        return f"РП-{year}-00001-01"

    async def _generate_transaction_number(self) -> str:
        """Генерация номера транзакции: ТС-YYYY-#####."""
        year = datetime.utcnow().year
        return f"ТС-{year}-00001"


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
        payment = await self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Платёж не найден")

        if payment.status == "cancelled":
            raise ValueError("Платёж уже отменён")

        # 2. Загрузить все распределения этого платежа
        distributions = await self.distribution_repository.get_by_payment(payment_id)

        # 3. Найти PersonalAccount
        member = await self._get_member_by_owner(payment.from_owner_id)
        if member:
            account = await self.account_repository.get_by_member(member.id)
        else:
            raise ValueError("PersonalAccount не найден")

        # 4. Отменить все PaymentDistribution и восстановить Accrual
        total_reversed = Decimal("0")
        for distribution in distributions:
            if distribution.status == "cancelled":
                continue

            # Обновить статус распределения
            distribution.status = "cancelled"
            await self.distribution_repository.update(distribution)

            # Восстановить paid_amount у Accrual
            accrual = await self.accrual_repository.get_by_financial_subject(
                distribution.financial_subject_id
            )
            if accrual:
                accrual.paid_amount -= distribution.amount
                accrual.status = "active"
                await self.accrual_repository.update(accrual)

            # Создать PersonalAccountTransaction (возврат)
            transaction = PersonalAccountTransaction(
                id=uuid4(),
                account_id=account.id,
                payment_id=payment.id,
                distribution_id=distribution.id,
                transaction_number=await self._generate_transaction_number(),
                transaction_date=datetime.utcnow(),
                amount=distribution.amount,  # Положительная сумма — возврат
                type="refund",
                description=f"Отмена распределения {distribution.id}: {reason}",
            )
            await self.account_repository.add_transaction(transaction)

            total_reversed += distribution.amount
            distribution.status = "cancelled"

        # 5. Обновить баланс счёта
        account.balance += total_reversed
        await self.account_repository.update(account)

        # 6. Обновить статус платежа
        payment.status = "cancelled"
        await self.payment_repository.update(payment)

        # 7. Доменное событие
        await self.event_dispatcher.dispatch(
            PaymentCancelled(
                payment_id=payment.id,
                reason=reason,
                reversed_amount=total_reversed,
            )
        )

        return CancelPaymentResult(
            payment_id=payment.id,
            reversed_amount=total_reversed,
            status="cancelled",
        )

    async def _get_member_by_owner(self, owner_id: UUID) -> Optional[Member]:
        """Получить Member по owner_id."""
        raise NotImplementedError("Требуется cooperative_id для поиска Member")

    async def _generate_transaction_number(self) -> str:
        """Генерация номера транзакции: ТС-YYYY-#####."""
        year = datetime.utcnow().year
        return f"ТС-{year}-00001"


class CreateDistributionRuleUseCase:
    """Создание правила распределения платежей."""

    def __init__(
        self,
        rule_repository: IDistributionRuleRepository,
        settings_module_repository: "ISettingsModuleRepository",
        event_dispatcher: "EventDispatcher",
    ):
        self.rule_repository = rule_repository
        self.settings_module_repository = settings_module_repository
        self.event_dispatcher = event_dispatcher

    async def execute(self, dto: DistributionRuleCreateDTO) -> PaymentDistributionRuleResponseDTO:
        # 1. Найти или создать SettingsModule для payment_distribution
        module = await self._get_or_create_settings_module(dto.cooperative_id)

        # 2. Проверить уникальность priority для cooperative
        existing_rules = await self.rule_repository.get_by_cooperative(
            dto.cooperative_id, is_active=True
        )
        if any(r.priority == dto.priority for r in existing_rules):
            raise ValueError("Правило с таким приоритетом уже существует")

        # 3. Проверить валидность rule_type
        if dto.rule_type in ["membership", "target", "additional"]:
            if not dto.contribution_type_id:
                raise ValueError("Требуется contribution_type_id для взносов")
        elif dto.rule_type in ["meter_water", "meter_electricity"]:
            if not dto.meter_type:
                raise ValueError("Требуется meter_type для счётчиков")

        # 4. Создать правило
        rule = PaymentDistributionRule(
            id=uuid4(),
            settings_module_id=module.id,
            rule_type=dto.rule_type,
            priority=dto.priority,
            contribution_type_id=dto.contribution_type_id,
            meter_type=dto.meter_type,
            is_active=True,
        )
        rule = await self.rule_repository.create(rule)

        # 5. Доменное событие
        await self.event_dispatcher.dispatch(
            DistributionRuleCreated(
                rule_id=rule.id,
                cooperative_id=dto.cooperative_id,
                rule_type=rule.rule_type,
                priority=rule.priority,
            )
        )

        # 6. Вернуть ответ
        return PaymentDistributionRuleResponseDTO(
            id=rule.id,
            settings_module_id=rule.settings_module_id,
            rule_type=rule.rule_type,
            priority=rule.priority,
            contribution_type_id=rule.contribution_type_id,
            meter_type=rule.meter_type,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    async def _get_or_create_settings_module(self, cooperative_id: UUID) -> SettingsModule:
        """Найти или создать SettingsModule для payment_distribution."""
        # Попытаться найти существующий
        modules = []  # TODO: Загрузить из repositories
        for module in modules:
            if module.module_name == "payment_distribution":
                return module

        # Создать новый
        module = SettingsModule(
            id=uuid4(),
            cooperative_id=cooperative_id,
            module_name="payment_distribution",
            is_active=True,
        )
        # TODO: Сохранить через repository
        return module


# =============================================================================
# Event Dispatcher
# =============================================================================


class EventDispatcher:
    """Диспетчер доменных событий."""

    async def dispatch(self, event):
        """Отправить событие (логирование, уведомления...)."""
        # TODO: Реализовать отправку событий
        pass


# =============================================================================
# Repository Interfaces (для type hinting)
# =============================================================================


class IPaymentRepository:
    """Репозиторий для платежей."""

    async def create(
        self,
        from_owner_id: UUID,
        total_amount: Decimal,
        payment_date: datetime,
        document_number: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PaymentEntity":
        """Создать платёж."""
        pass

    async def get_by_id(self, payment_id: UUID) -> Optional["PaymentEntity"]:
        """Получить платёж по ID."""
        pass

    async def update(self, payment: "PaymentEntity") -> "PaymentEntity":
        """Обновить платёж."""
        pass

    async def get_distributions(self, payment_id: UUID) -> List[PaymentDistributionResponseDTO]:
        """Получить распределения платежа."""
        pass


class IAccrualRepository:
    """Репозиторий для начислений."""

    async def get_unpaid_by_member(self, member_id: UUID) -> List["Accrual"]:
        """Получить непогашенные начисления члена."""
        pass

    async def update(self, accrual: "Accrual") -> "Accrual":
        """Обновить начисление."""
        pass

    async def get_by_financial_subject(self, financial_subject_id: UUID) -> Optional["Accrual"]:
        """Получить начисление по финансовому субъекту."""
        pass


class IFinancialSubjectRepository:
    """Репозиторий для финансовых субъектов."""

    pass


class ISettingsModuleRepository:
    """Репозиторий для модулей настроек."""

    pass
