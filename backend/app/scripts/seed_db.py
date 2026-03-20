"""Заполнение БД тестовыми данными для разработки и демо.

Запуск из каталога backend:
  python -m app.scripts.seed_db

Создаёт: 2 СТ, 5 владельцев, 10 участков с правами собственности,
финансовые субъекты, виды взносов, категории расходов, начисления и платежи,
расходы, 3 счётчика с показаниями, 3 пользователя (admin, chairman, treasurer).
Все сущности создаются только если ещё не существуют (идемпотентный скрипт).
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.modules.accruals.infrastructure.models import AccrualModel, ContributionTypeModel
from app.modules.administration.infrastructure.models import AppUserModel
from app.modules.cooperative_core.infrastructure.models import CooperativeModel
from app.modules.expenses.infrastructure.models import ExpenseCategoryModel, ExpenseModel
from app.modules.financial_core.infrastructure.models import FinancialSubjectModel
from app.modules.land_management.infrastructure.models import (
    LandPlotModel,
    OwnerModel,
    PlotOwnershipModel,
)
from app.modules.meters.infrastructure.models import MeterModel, MeterReadingModel
from app.modules.payments.infrastructure.models import PaymentModel


async def seed(session) -> None:
    """Создаёт все тестовые сущности в переданной сессии (идемпотентно)."""
    # 2 СТ (только если нет)
    result = await session.execute(
        select(CooperativeModel).where(CooperativeModel.unp.in_(["100000001", "100000002"]))
    )
    existing_coops = result.scalars().all()
    if len(existing_coops) == 2:
        print("[INFO] СТ уже существуют, пропускаем создание")
        coop_romashka = existing_coops[0]
        coop_vasilek = existing_coops[1]
    else:
        coop_romashka = CooperativeModel(
            name='СТ "Ромашка"', unp="100000001", address="Минский р-н, д. Ромашки"
        )
        coop_vasilek = CooperativeModel(
            name='СТ "Василёк"', unp="100000002", address="Минский р-н, д. Васильки"
        )
        session.add_all([coop_romashka, coop_vasilek])
        await session.flush()
        print("[OK] Создано 2 СТ")

    # 5 владельцев: 3 физ., 2 юр.
    owners = [
        OwnerModel(
            owner_type="physical",
            name="Иванов Иван Иванович",
            tax_id="123456789A",
            contact_phone="+375291111111",
        ),
        OwnerModel(
            owner_type="physical",
            name="Петрова Мария Сергеевна",
            tax_id="123456789B",
            contact_phone="+375292222222",
        ),
        OwnerModel(owner_type="physical", name="Сидоров Пётр Алексеевич", tax_id="123456789C"),
        OwnerModel(
            owner_type="legal",
            name="ООО «Дачник»",
            tax_id="123456789",
            contact_email="dachnik@example.by",
        ),
        OwnerModel(owner_type="legal", name="ИП Козлов", tax_id="987654321"),
    ]
    session.add_all(owners)
    await session.flush()

    # 10 участков: 5 в Ромашке, 5 в Васильке
    plots = []
    for i, coop in enumerate([coop_romashka, coop_vasilek]):
        for j in range(1, 6):
            num = i * 5 + j
            plot = LandPlotModel(
                cooperative_id=coop.id,
                plot_number=str(num),
                area_sqm=Decimal("600.00") + Decimal(num * 10),
                cadastral_number=f"21201{num:06d}" if num <= 999999 else None,
                status="active",
            )
            session.add(plot)
            plots.append(plot)
    await session.flush()

    # PlotOwnership: каждому участку — один основной владелец (циклически из 5)
    today = date.today()
    for idx, plot in enumerate(plots):
        owner = owners[idx % 5]
        session.add(
            PlotOwnershipModel(
                land_plot_id=plot.id,
                owner_id=owner.id,
                share_numerator=1,
                share_denominator=1,
                is_primary=True,
                valid_from=today.replace(year=today.year - 2),
                valid_to=None,
            )
        )
    await session.flush()

    # FinancialSubject для каждого участка
    subjects = []
    for i, plot in enumerate(plots):
        coop = coop_romashka if plot.cooperative_id == coop_romashka.id else coop_vasilek
        fs = FinancialSubjectModel(
            subject_type="LAND_PLOT",
            subject_id=plot.id,
            cooperative_id=coop.id,
            code=f"FS-SEED-{i + 1:03d}",
            status="active",
        )
        session.add(fs)
        subjects.append(fs)
    await session.flush()

    # 3 вида взносов
    ctypes = [
        ContributionTypeModel(name="Членский", code="MEMBER", description="Членский взнос"),
        ContributionTypeModel(name="Целевой", code="TARGET", description="Целевой взнос"),
        ContributionTypeModel(
            name="Электроэнергия", code="ELECTRICITY", description="Взнос за электроэнергию"
        ),
    ]
    session.add_all(ctypes)
    await session.flush()

    # 3 категории расходов
    ecats = [
        ExpenseCategoryModel(name="Дороги", code="ROADS", description="Ремонт и содержание дорог"),
        ExpenseCategoryModel(name="Зарплата", code="SALARY", description="Оплата труда"),
        ExpenseCategoryModel(name="Материалы", code="MATERIALS", description="Стройматериалы"),
    ]
    session.add_all(ecats)
    await session.flush()

    # Несколько начислений и платежей (по первым 4 субъектам)
    period_start = today.replace(month=1, day=1)
    for i in range(4):
        subj = subjects[i]
        ct = ctypes[i % 3]
        owner = owners[i % 5]
        session.add(
            AccrualModel(
                financial_subject_id=subj.id,
                contribution_type_id=ct.id,
                amount=Decimal("500.00") + Decimal(i * 100),
                accrual_date=today,
                period_start=period_start,
                period_end=today,
                due_date=today.replace(day=today.day + 30),  # Срок оплаты +30 дней
                status="applied",
                operation_number=f"ACC-SEED-{i + 1}",
            )
        )
    await session.flush()

    result = await session.execute(select(AccrualModel).order_by(AccrualModel.id))
    accruals = list(result.scalars().all())

    for i, acc in enumerate(accruals[:4]):
        owner = owners[i % 5]
        session.add(
            PaymentModel(
                financial_subject_id=acc.financial_subject_id,
                payer_owner_id=owner.id,
                amount=Decimal("300.00") + Decimal(i * 50),
                payment_date=today,
                document_number=f"П-{i + 1}",
                status="confirmed",
                operation_number=f"PAY-SEED-{i + 1}",
            )
        )
    await session.flush()

    # Несколько расходов
    for idx, coop in enumerate([coop_romashka, coop_vasilek]):
        session.add(
            ExpenseModel(
                cooperative_id=coop.id,
                category_id=ecats[0].id,
                amount=Decimal("10000.00"),
                expense_date=today,
                document_number="Р-1",
                description="Ремонт дороги",
                status="confirmed",
                operation_number=f"EXP-SEED-{idx * 2 + 1}",
            )
        )
        session.add(
            ExpenseModel(
                cooperative_id=coop.id,
                category_id=ecats[1].id,
                amount=Decimal("5000.00"),
                expense_date=today,
                description="Зарплата председателя",
                status="confirmed",
                operation_number=f"EXP-SEED-{idx * 2 + 2}",
            )
        )
    await session.flush()

    # 3 счётчика с показаниями (привязываем к первым 3 владельцам)
    meters = []
    for i, owner in enumerate(owners[:3]):
        m = MeterModel(
            owner_id=owner.id,
            meter_type="ELECTRICITY" if i % 2 == 0 else "WATER",
            serial_number=f"M-{1000 + i}",
            installation_date=datetime.now(UTC),
            status="active",
        )
        session.add(m)
        meters.append(m)
    await session.flush()

    rd = datetime.now(UTC)
    for m in meters:
        session.add(
            MeterReadingModel(
                meter_id=m.id,
                reading_value=Decimal("100.5") + Decimal(meters.index(m) * 10),
                reading_date=rd,
            )
        )
    await session.flush()

    # 3 пользователя: admin (без СТ), chairman и treasurer (с СТ Ромашка) — только если ещё нет
    for username in ("admin", "chairman", "treasurer"):
        result = await session.execute(
            select(AppUserModel).where(AppUserModel.username == username)
        )
        if result.scalar_one_or_none() is not None:
            continue
        role = "admin" if username == "admin" else username
        cooperative_id = None if username == "admin" else coop_romashka.id
        user = AppUserModel(
            username=username,
            email=f"{username}@controlling.local",
            hashed_password=get_password_hash(username),
            role=role,
            cooperative_id=cooperative_id,
            is_active=True,
        )
        session.add(user)
    await session.flush()


async def main() -> int:
    async with async_session_maker() as session:
        try:
            await seed(session)
            await session.commit()
            print("[OK] Seed выполнен (или пропущен, если данные уже есть).")
            print("Пользователи: admin/admin, chairman/chairman, treasurer/treasurer")
            return 0
        except Exception as e:
            await session.rollback()
            if "duplicate key" in str(e).lower() or "unique violation" in str(e).lower():
                print("[INFO] Seed пропущен: данные уже существуют в БД")
                return 0
            print(f"[ERROR] Ошибка при seed: {e}", file=sys.stderr)
            raise


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
