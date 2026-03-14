"""
Repository interfaces for Payment Distribution module.

Интерфейсы репозиториев (контракты) без реализации.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .entities import (
    ContributionTypeSettings,
    Member,
    MeterTariff,
    PaymentDistribution,
    PaymentDistributionRule,
    PersonalAccount,
    PersonalAccountTransaction,
    SettingsModule,
)


class IMemberRepository(ABC):
    """Репозиторий для членов СТ."""

    @abstractmethod
    async def create(self, member: Member) -> Member:
        """Создать члена СТ."""
        pass

    @abstractmethod
    async def get_by_id(self, member_id: UUID) -> Optional[Member]:
        """Получить члена СТ по ID."""
        pass

    @abstractmethod
    async def get_by_owner_and_cooperative(
        self, owner_id: UUID, cooperative_id: UUID
    ) -> Optional[Member]:
        """Получить члена СТ по владельцу и товариществу."""
        pass

    @abstractmethod
    async def get_by_cooperative(
        self, cooperative_id: UUID, status: Optional[str] = None
    ) -> List[Member]:
        """Получить всех членов СТ."""
        pass

    @abstractmethod
    async def update(self, member: Member) -> Member:
        """Обновить члена СТ."""
        pass


class IPersonalAccountRepository(ABC):
    """Репозиторий для лицевых счетов."""

    @abstractmethod
    async def create(self, account: PersonalAccount) -> PersonalAccount:
        """Создать лицевой счёт."""
        pass

    @abstractmethod
    async def get_by_id(self, account_id: UUID) -> Optional[PersonalAccount]:
        """Получить счёт по ID."""
        pass

    @abstractmethod
    async def get_by_member(self, member_id: UUID) -> Optional[PersonalAccount]:
        """Получить счёт члена СТ."""
        pass

    @abstractmethod
    async def get_by_cooperative(
        self, cooperative_id: UUID, status: Optional[str] = None
    ) -> List[PersonalAccount]:
        """Получить счета по товариществу."""
        pass

    @abstractmethod
    async def update(self, account: PersonalAccount) -> PersonalAccount:
        """Обновить счёт."""
        pass

    @abstractmethod
    async def add_transaction(
        self, transaction: PersonalAccountTransaction
    ) -> PersonalAccountTransaction:
        """Добавить операцию по счёту."""
        pass

    @abstractmethod
    async def get_transactions(
        self, account_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[PersonalAccountTransaction]:
        """Получить историю операций счёта."""
        pass


class IPaymentDistributionRepository(ABC):
    """Репозиторий для распределения платежей."""

    @abstractmethod
    async def create(self, distribution: PaymentDistribution) -> PaymentDistribution:
        """Создать распределение платежа."""
        pass

    @abstractmethod
    async def get_by_payment(self, payment_id: UUID) -> List[PaymentDistribution]:
        """Получить распределения по платежу."""
        pass

    @abstractmethod
    async def get_by_id(self, distribution_id: UUID) -> Optional[PaymentDistribution]:
        """Получить распределение по ID."""
        pass

    @abstractmethod
    async def update(self, distribution: PaymentDistribution) -> PaymentDistribution:
        """Обновить распределение."""
        pass


class IDistributionRuleRepository(ABC):
    """Репозиторий для правил распределения."""

    @abstractmethod
    async def create(self, rule: PaymentDistributionRule) -> PaymentDistributionRule:
        """Создать правило распределения."""
        pass

    @abstractmethod
    async def get_by_cooperative(
        self, cooperative_id: UUID, is_active: bool = True
    ) -> List[PaymentDistributionRule]:
        """Получить правила для товарищества."""
        pass

    @abstractmethod
    async def update(self, rule: PaymentDistributionRule) -> PaymentDistributionRule:
        """Обновить правило."""
        pass

    @abstractmethod
    async def delete(self, rule_id: UUID) -> None:
        """Удалить правило."""
        pass


class ISettingsModuleRepository(ABC):
    """Репозиторий для модулей настроек."""

    @abstractmethod
    async def create(self, module: SettingsModule) -> SettingsModule:
        """Создать модуль настроек."""
        pass

    @abstractmethod
    async def get_by_id(self, module_id: UUID) -> Optional[SettingsModule]:
        """Получить модуль по ID."""
        pass

    @abstractmethod
    async def get_by_cooperative(
        self, cooperative_id: UUID, module_name: Optional[str] = None
    ) -> List[SettingsModule]:
        """Получить модули для товарищества."""
        pass

    @abstractmethod
    async def update(self, module: SettingsModule) -> SettingsModule:
        """Обновить модуль."""
        pass


class IContributionTypeSettingsRepository(ABC):
    """Репозиторий для настроек видов взносов."""

    @abstractmethod
    async def create(self, settings: ContributionTypeSettings) -> ContributionTypeSettings:
        """Создать настройку вида взноса."""
        pass

    @abstractmethod
    async def get_by_module(self, settings_module_id: UUID) -> List[ContributionTypeSettings]:
        """Получить настройки по модулю."""
        pass

    @abstractmethod
    async def update(self, settings: ContributionTypeSettings) -> ContributionTypeSettings:
        """Обновить настройку."""
        pass


class IMeterTariffRepository(ABC):
    """Репозиторий для тарифов на ресурсы."""

    @abstractmethod
    async def create(self, tariff: MeterTariff) -> MeterTariff:
        """Создать тариф."""
        pass

    @abstractmethod
    async def get_by_module(
        self, settings_module_id: UUID, meter_type: Optional[str] = None
    ) -> List[MeterTariff]:
        """Получить тарифы по модулю."""
        pass

    @abstractmethod
    async def update(self, tariff: MeterTariff) -> MeterTariff:
        """Обновить тариф."""
        pass
