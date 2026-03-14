"""Tests for Payment Distribution module."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4


class TestMemberEntity:
    """Тесты для сущности Member."""

    def test_member_create(self):
        """Создание члена СТ."""
        from app.modules.payment_distribution.domain.entities import Member

        member = Member(
            id=uuid4(),
            owner_id=uuid4(),
            cooperative_id=uuid4(),
            status="active",
            joined_date=datetime.utcnow(),
        )

        assert member.status == "active"
        assert member.id is not None


class TestPersonalAccountEntity:
    """Тесты для сущности PersonalAccount."""

    def test_account_create(self):
        """Создание лицевого счёта."""
        from app.modules.payment_distribution.domain.entities import PersonalAccount

        account = PersonalAccount(
            id=uuid4(),
            member_id=uuid4(),
            cooperative_id=uuid4(),
            account_number="LS-2026-00001",
            balance=Decimal("0.00"),
            status="active",
            opened_at=datetime.utcnow(),
        )

        assert account.balance == Decimal("0.00")
        assert account.status == "active"
        assert account.account_number == "LS-2026-00001"

    def test_account_credit(self):
        """Зачисление на счёт."""
        from app.modules.payment_distribution.domain.entities import PersonalAccount

        account = PersonalAccount(
            id=uuid4(),
            member_id=uuid4(),
            cooperative_id=uuid4(),
            account_number="LS-2026-00002",
            balance=Decimal("0.00"),
            status="active",
            opened_at=datetime.utcnow(),
        )

        account.balance += Decimal("100.00")
        assert account.balance == Decimal("100.00")

    def test_account_debit(self):
        """Списание со счёта."""
        from app.modules.payment_distribution.domain.entities import PersonalAccount

        account = PersonalAccount(
            id=uuid4(),
            member_id=uuid4(),
            cooperative_id=uuid4(),
            account_number="LS-2026-00003",
            balance=Decimal("100.00"),
            status="active",
            opened_at=datetime.utcnow(),
        )

        account.balance -= Decimal("50.00")
        assert account.balance == Decimal("50.00")


class TestPaymentDistributionEntity:
    """Тесты для сущности PaymentDistribution."""

    def test_distribution_create(self):
        """Создание распределения платежа."""
        from app.modules.payment_distribution.domain.entities import PaymentDistribution

        distribution = PaymentDistribution(
            id=uuid4(),
            payment_id=uuid4(),
            financial_subject_id=uuid4(),
            distribution_number="РП-2026-00001-01",
            distributed_at=datetime.utcnow(),
            amount=Decimal("50.00"),
            priority=1,
            status="applied",
        )

        assert distribution.amount == Decimal("50.00")
        assert distribution.priority == 1
        assert distribution.status == "applied"


class TestPaymentDistributionRule:
    """Тесты для правила распределения."""

    def test_rule_create(self):
        """Создание правила распределения."""
        from app.modules.payment_distribution.domain.entities import PaymentDistributionRule

        rule = PaymentDistributionRule(
            id=uuid4(),
            settings_module_id=uuid4(),
            rule_type="membership",
            priority=1,
            is_active=True,
        )

        assert rule.rule_type == "membership"
        assert rule.priority == 1
        assert rule.is_active is True

    def test_rule_priority_order(self):
        """Сортировка правил по приоритету."""
        from app.modules.payment_distribution.domain.entities import PaymentDistributionRule

        rules = [
            PaymentDistributionRule(
                id=uuid4(),
                settings_module_id=uuid4(),
                rule_type="target",
                priority=2,
            ),
            PaymentDistributionRule(
                id=uuid4(),
                settings_module_id=uuid4(),
                rule_type="membership",
                priority=1,
            ),
            PaymentDistributionRule(
                id=uuid4(),
                settings_module_id=uuid4(),
                rule_type="meter_water",
                priority=3,
            ),
        ]

        # Сортировка по приоритету (1 = высший)
        rules.sort(key=lambda r: r.priority)

        assert rules[0].rule_type == "membership"
        assert rules[1].rule_type == "target"
        assert rules[2].rule_type == "meter_water"


class TestDomainEvents:
    """Тесты для доменных событий."""

    def test_member_created_event(self):
        """Событие создания члена СТ."""
        from app.modules.payment_distribution.domain.events import MemberCreated

        event = MemberCreated(
            member_id=uuid4(),
            owner_id=uuid4(),
            cooperative_id=uuid4(),
        )

        assert event.member_id is not None
        assert event.timestamp is not None

    def test_payment_received_event(self):
        """Событие получения платежа."""
        from decimal import Decimal

        from app.modules.payment_distribution.domain.events import PaymentReceived

        event = PaymentReceived(
            payment_id=uuid4(),
            owner_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("100.00"),
        )

        assert event.amount == Decimal("100.00")

    def test_payment_distributed_event(self):
        """Событие распределения платежа."""
        from decimal import Decimal

        from app.modules.payment_distribution.domain.events import PaymentDistributed

        event = PaymentDistributed(
            payment_id=uuid4(),
            distributions=[uuid4(), uuid4()],
            total_distributed=Decimal("100.00"),
            remaining_balance=Decimal("0.00"),
        )

        assert event.total_distributed == Decimal("100.00")
        assert len(event.distributions) == 2
