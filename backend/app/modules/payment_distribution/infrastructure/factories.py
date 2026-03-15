"""
Factories for Payment Distribution module.

Фабрики для создания репозиториев.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.repositories import (
    IContributionTypeSettingsRepository,
    IDistributionRuleRepository,
    IMemberRepository,
    IMeterTariffRepository,
    IPaymentDistributionRepository,
    IPersonalAccountRepository,
    ISettingsModuleRepository,
)
from .repositories import (
    ContributionTypeSettingsRepository,
    DistributionRuleRepository,
    MemberRepository,
    MeterTariffRepository,
    PaymentDistributionRepository,
    PersonalAccountRepository,
    SettingsModuleRepository,
)


def create_member_repository(session: AsyncSession) -> IMemberRepository:
    """Создать репозиторий Member."""
    return MemberRepository(session)


def create_personal_account_repository(session: AsyncSession) -> IPersonalAccountRepository:
    """Создать репозиторий PersonalAccount."""
    return PersonalAccountRepository(session)


def create_payment_distribution_repository(session: AsyncSession) -> IPaymentDistributionRepository:
    """Создать репозиторий PaymentDistribution."""
    return PaymentDistributionRepository(session)


def create_distribution_rule_repository(session: AsyncSession) -> IDistributionRuleRepository:
    """Создать репозиторий DistributionRule."""
    return DistributionRuleRepository(session)


def create_settings_module_repository(session: AsyncSession) -> ISettingsModuleRepository:
    """Создать репозиторий SettingsModule."""
    return SettingsModuleRepository(session)


def create_contribution_type_settings_repository(
    session: AsyncSession,
) -> IContributionTypeSettingsRepository:
    """Создать репозиторий ContributionTypeSettings."""
    return ContributionTypeSettingsRepository(session)


def create_meter_tariff_repository(session: AsyncSession) -> IMeterTariffRepository:
    """Создать репозиторий MeterTariff."""
    return MeterTariffRepository(session)
