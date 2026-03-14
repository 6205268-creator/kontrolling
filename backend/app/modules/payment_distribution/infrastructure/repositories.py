"""
Repository implementations for Payment Distribution module.

Реализация репозиториев для работы с БД.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import (
    ContributionTypeSettings,
    Member,
    MeterTariff,
    PaymentDistribution,
    PaymentDistributionRule,
    PersonalAccount,
    PersonalAccountTransaction,
    SettingsModule,
)
from ..domain.repositories import (
    IContributionTypeSettingsRepository,
    IDistributionRuleRepository,
    IMemberRepository,
    IMeterTariffRepository,
    IPaymentDistributionRepository,
    IPersonalAccountRepository,
    ISettingsModuleRepository,
)
from .models import (
    ContributionTypeSettingsModel,
    MemberModel,
    MeterTariffModel,
    PaymentDistributionModel,
    PaymentDistributionRuleModel,
    PersonalAccountModel,
    PersonalAccountTransactionModel,
    SettingsModuleModel,
)


class MemberRepository(IMemberRepository):
    """Репозиторий для членов СТ."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, member: Member) -> Member:
        model = MemberModel(
            id=member.id,
            owner_id=member.owner_id,
            cooperative_id=member.cooperative_id,
            status=member.status,
            joined_date=member.joined_date,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return member

    async def get_by_id(self, member_id: UUID) -> Optional[Member]:
        result = await self.session.execute(select(MemberModel).where(MemberModel.id == member_id))
        model = result.scalar_one_or_none()
        if model:
            return self._map_to_entity(model)
        return None

    async def get_by_owner_and_cooperative(
        self, owner_id: UUID, cooperative_id: UUID
    ) -> Optional[Member]:
        result = await self.session.execute(
            select(MemberModel).where(
                MemberModel.owner_id == owner_id,
                MemberModel.cooperative_id == cooperative_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            return self._map_to_entity(model)
        return None

    async def get_by_cooperative(
        self, cooperative_id: UUID, status: Optional[str] = None
    ) -> List[Member]:
        query = select(MemberModel).where(MemberModel.cooperative_id == cooperative_id)
        if status:
            query = query.where(MemberModel.status == status)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def update(self, member: Member) -> Member:
        model = await self._get_model(member.id)
        if not model:
            raise ValueError("Member not found")

        model.status = member.status
        model.joined_date = member.joined_date
        model.updated_at = member.updated_at

        await self.session.flush()
        return member

    def _map_to_entity(self, model: MemberModel) -> Member:
        return Member(
            id=model.id,
            owner_id=model.owner_id,
            cooperative_id=model.cooperative_id,
            status=model.status,
            joined_date=model.joined_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_model(self, member_id: UUID) -> Optional[MemberModel]:
        result = await self.session.execute(select(MemberModel).where(MemberModel.id == member_id))
        return result.scalar_one_or_none()


class PersonalAccountRepository(IPersonalAccountRepository):
    """Репозиторий для лицевых счетов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, account: PersonalAccount) -> PersonalAccount:
        model = PersonalAccountModel(
            id=account.id,
            member_id=account.member_id,
            cooperative_id=account.cooperative_id,
            account_number=account.account_number,
            balance=account.balance,
            status=account.status,
            opened_at=account.opened_at,
            closed_at=account.closed_at,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return account

    async def get_by_id(self, account_id: UUID) -> Optional[PersonalAccount]:
        result = await self.session.execute(
            select(PersonalAccountModel).where(PersonalAccountModel.id == account_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return self._map_to_entity(model)
        return None

    async def get_by_member(self, member_id: UUID) -> Optional[PersonalAccount]:
        result = await self.session.execute(
            select(PersonalAccountModel).where(PersonalAccountModel.member_id == member_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return self._map_to_entity(model)
        return None

    async def get_by_cooperative(
        self, cooperative_id: UUID, status: Optional[str] = None
    ) -> List[PersonalAccount]:
        query = select(PersonalAccountModel).where(
            PersonalAccountModel.cooperative_id == cooperative_id
        )
        if status:
            query = query.where(PersonalAccountModel.status == status)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def update(self, account: PersonalAccount) -> PersonalAccount:
        model = await self._get_model(account.id)
        if not model:
            raise ValueError("PersonalAccount not found")

        model.balance = account.balance
        model.status = account.status
        model.closed_at = account.closed_at
        model.updated_at = account.updated_at

        await self.session.flush()
        return account

    async def add_transaction(
        self, transaction: PersonalAccountTransaction
    ) -> PersonalAccountTransaction:
        model = PersonalAccountTransactionModel(
            id=transaction.id,
            account_id=transaction.account_id,
            payment_id=transaction.payment_id,
            distribution_id=transaction.distribution_id,
            transaction_number=transaction.transaction_number,
            transaction_date=transaction.transaction_date,
            amount=transaction.amount,
            type=transaction.type,
            description=transaction.description,
            created_at=transaction.created_at,
        )
        self.session.add(model)
        await self.session.flush()
        return transaction

    async def get_transactions(
        self, account_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[PersonalAccountTransaction]:
        query = (
            select(PersonalAccountTransactionModel)
            .where(PersonalAccountTransactionModel.account_id == account_id)
            .order_by(PersonalAccountTransactionModel.transaction_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._map_transaction_to_entity(m) for m in models]

    def _map_to_entity(self, model: PersonalAccountModel) -> PersonalAccount:
        return PersonalAccount(
            id=model.id,
            member_id=model.member_id,
            cooperative_id=model.cooperative_id,
            account_number=model.account_number,
            balance=model.balance,
            status=model.status,
            opened_at=model.opened_at,
            closed_at=model.closed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _map_transaction_to_entity(
        self, model: PersonalAccountTransactionModel
    ) -> PersonalAccountTransaction:
        return PersonalAccountTransaction(
            id=model.id,
            account_id=model.account_id,
            payment_id=model.payment_id,
            distribution_id=model.distribution_id,
            transaction_number=model.transaction_number,
            transaction_date=model.transaction_date,
            amount=model.amount,
            type=model.type,
            description=model.description,
            created_at=model.created_at,
        )

    async def _get_model(self, account_id: UUID) -> Optional[PersonalAccountModel]:
        result = await self.session.execute(
            select(PersonalAccountModel).where(PersonalAccountModel.id == account_id)
        )
        return result.scalar_one_or_none()


class PaymentDistributionRepository(IPaymentDistributionRepository):
    """Репозиторий для распределения платежей."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, distribution: PaymentDistribution) -> PaymentDistribution:
        model = PaymentDistributionModel(
            id=distribution.id,
            payment_id=distribution.payment_id,
            financial_subject_id=distribution.financial_subject_id,
            distribution_number=distribution.distribution_number,
            distributed_at=distribution.distributed_at,
            amount=distribution.amount,
            priority=distribution.priority,
            status=distribution.status,
            created_at=distribution.created_at,
            updated_at=distribution.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return distribution

    async def get_by_payment(self, payment_id: UUID) -> List[PaymentDistribution]:
        result = await self.session.execute(
            select(PaymentDistributionModel).where(
                PaymentDistributionModel.payment_id == payment_id
            )
        )
        models = result.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def get_by_id(self, distribution_id: UUID) -> Optional[PaymentDistribution]:
        result = await self.session.execute(
            select(PaymentDistributionModel).where(PaymentDistributionModel.id == distribution_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return self._map_to_entity(model)
        return None

    async def update(self, distribution: PaymentDistribution) -> PaymentDistribution:
        model = await self._get_model(distribution.id)
        if not model:
            raise ValueError("PaymentDistribution not found")

        model.status = distribution.status
        model.amount = distribution.amount
        model.updated_at = distribution.updated_at

        await self.session.flush()
        return distribution

    def _map_to_entity(self, model: PaymentDistributionModel) -> PaymentDistribution:
        return PaymentDistribution(
            id=model.id,
            payment_id=model.payment_id,
            financial_subject_id=model.financial_subject_id,
            distribution_number=model.distribution_number,
            distributed_at=model.distributed_at,
            amount=model.amount,
            priority=model.priority,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_model(self, distribution_id: UUID) -> Optional[PaymentDistributionModel]:
        result = await self.session.execute(
            select(PaymentDistributionModel).where(PaymentDistributionModel.id == distribution_id)
        )
        return result.scalar_one_or_none()


class DistributionRuleRepository(IDistributionRuleRepository):
    """Репозиторий для правил распределения."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, rule: PaymentDistributionRule) -> PaymentDistributionRule:
        model = PaymentDistributionRuleModel(
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
        self.session.add(model)
        await self.session.flush()
        return rule

    async def get_by_cooperative(
        self, cooperative_id: UUID, is_active: bool = True
    ) -> List[PaymentDistributionRule]:
        # Join with SettingsModule to filter by cooperative
        result = await self.session.execute(
            select(PaymentDistributionRuleModel)
            .join(SettingsModuleModel)
            .where(
                SettingsModuleModel.cooperative_id == cooperative_id,
                PaymentDistributionRuleModel.is_active == is_active,
            )
            .order_by(PaymentDistributionRuleModel.priority)
        )
        models = result.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def update(self, rule: PaymentDistributionRule) -> PaymentDistributionRule:
        model = await self._get_model(rule.id)
        if not model:
            raise ValueError("PaymentDistributionRule not found")

        model.rule_type = rule.rule_type
        model.priority = rule.priority
        model.contribution_type_id = rule.contribution_type_id
        model.meter_type = rule.meter_type
        model.is_active = rule.is_active
        model.updated_at = rule.updated_at

        await self.session.flush()
        return rule

    async def delete(self, rule_id: UUID) -> None:
        model = await self._get_model(rule_id)
        if model:
            await self.session.delete(model)

    def _map_to_entity(self, model: PaymentDistributionRuleModel) -> PaymentDistributionRule:
        return PaymentDistributionRule(
            id=model.id,
            settings_module_id=model.settings_module_id,
            rule_type=model.rule_type,
            priority=model.priority,
            contribution_type_id=model.contribution_type_id,
            meter_type=model.meter_type,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_model(self, rule_id: UUID) -> Optional[PaymentDistributionRuleModel]:
        result = await self.session.execute(
            select(PaymentDistributionRuleModel).where(PaymentDistributionRuleModel.id == rule_id)
        )
        return result.scalar_one_or_none()


class SettingsModuleRepository(ISettingsModuleRepository):
    """Репозиторий для модулей настроек."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, module: SettingsModule) -> SettingsModule:
        model = SettingsModuleModel(
            id=module.id,
            cooperative_id=module.cooperative_id,
            module_name=module.module_name,
            is_active=module.is_active,
            created_at=module.created_at,
            updated_at=module.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return module

    async def get_by_id(self, module_id: UUID) -> Optional[SettingsModule]:
        result = await self.session.execute(
            select(SettingsModuleModel).where(SettingsModuleModel.id == module_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return self._map_to_entity(model)
        return None

    async def get_by_cooperative(
        self, cooperative_id: UUID, module_name: Optional[str] = None
    ) -> List[SettingsModule]:
        query = select(SettingsModuleModel).where(
            SettingsModuleModel.cooperative_id == cooperative_id
        )
        if module_name:
            query = query.where(SettingsModuleModel.module_name == module_name)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def update(self, module: SettingsModule) -> SettingsModule:
        model = await self._get_model(module.id)
        if not model:
            raise ValueError("SettingsModule not found")

        model.module_name = module.module_name
        model.is_active = module.is_active
        model.updated_at = module.updated_at

        await self.session.flush()
        return module

    def _map_to_entity(self, model: SettingsModuleModel) -> SettingsModule:
        return SettingsModule(
            id=model.id,
            cooperative_id=model.cooperative_id,
            module_name=model.module_name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_model(self, module_id: UUID) -> Optional[SettingsModuleModel]:
        result = await self.session.execute(
            select(SettingsModuleModel).where(SettingsModuleModel.id == module_id)
        )
        return result.scalar_one_or_none()


class ContributionTypeSettingsRepository(IContributionTypeSettingsRepository):
    """Репозиторий для настроек видов взносов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, settings: ContributionTypeSettings) -> ContributionTypeSettings:
        model = ContributionTypeSettingsModel(
            id=settings.id,
            settings_module_id=settings.settings_module_id,
            contribution_type_id=settings.contribution_type_id,
            default_amount=settings.default_amount,
            is_mandatory=settings.is_mandatory,
            calculation_period=settings.calculation_period,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return settings

    async def get_by_module(self, settings_module_id: UUID) -> List[ContributionTypeSettings]:
        result = await self.session.execute(
            select(ContributionTypeSettingsModel).where(
                ContributionTypeSettingsModel.settings_module_id == settings_module_id
            )
        )
        models = result.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def update(self, settings: ContributionTypeSettings) -> ContributionTypeSettings:
        model = await self._get_model(settings.id)
        if not model:
            raise ValueError("ContributionTypeSettings not found")

        model.default_amount = settings.default_amount
        model.is_mandatory = settings.is_mandatory
        model.calculation_period = settings.calculation_period
        model.updated_at = settings.updated_at

        await self.session.flush()
        return settings

    def _map_to_entity(self, model: ContributionTypeSettingsModel) -> ContributionTypeSettings:
        return ContributionTypeSettings(
            id=model.id,
            settings_module_id=model.settings_module_id,
            contribution_type_id=model.contribution_type_id,
            default_amount=model.default_amount,
            is_mandatory=model.is_mandatory,
            calculation_period=model.calculation_period,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_model(self, settings_id: UUID) -> Optional[ContributionTypeSettingsModel]:
        result = await self.session.execute(
            select(ContributionTypeSettingsModel).where(
                ContributionTypeSettingsModel.id == settings_id
            )
        )
        return result.scalar_one_or_none()


class MeterTariffRepository(IMeterTariffRepository):
    """Репозиторий для тарифов на ресурсы."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tariff: MeterTariff) -> MeterTariff:
        model = MeterTariffModel(
            id=tariff.id,
            settings_module_id=tariff.settings_module_id,
            meter_type=tariff.meter_type,
            tariff_per_unit=tariff.tariff_per_unit,
            valid_from=tariff.valid_from,
            valid_to=tariff.valid_to,
            created_at=tariff.created_at,
            updated_at=tariff.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return tariff

    async def get_by_module(
        self, settings_module_id: UUID, meter_type: Optional[str] = None
    ) -> List[MeterTariff]:
        query = select(MeterTariffModel).where(
            MeterTariffModel.settings_module_id == settings_module_id
        )
        if meter_type:
            query = query.where(MeterTariffModel.meter_type == meter_type)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._map_to_entity(m) for m in models]

    async def update(self, tariff: MeterTariff) -> MeterTariff:
        model = await self._get_model(tariff.id)
        if not model:
            raise ValueError("MeterTariff not found")

        model.tariff_per_unit = tariff.tariff_per_unit
        model.valid_from = tariff.valid_from
        model.valid_to = tariff.valid_to
        model.updated_at = tariff.updated_at

        await self.session.flush()
        return tariff

    def _map_to_entity(self, model: MeterTariffModel) -> MeterTariff:
        return MeterTariff(
            id=model.id,
            settings_module_id=model.settings_module_id,
            meter_type=model.meter_type,
            tariff_per_unit=model.tariff_per_unit,
            valid_from=model.valid_from,
            valid_to=model.valid_to,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_model(self, tariff_id: UUID) -> Optional[MeterTariffModel]:
        result = await self.session.execute(
            select(MeterTariffModel).where(MeterTariffModel.id == tariff_id)
        )
        return result.scalar_one_or_none()
