import uuid
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cooperative import Cooperative
from app.models.financial_subject import FinancialSubject, generate_financial_subject_code


@pytest.mark.asyncio
async def test_create_financial_subject_for_land_plot(test_db: AsyncSession) -> None:
    """Создание FinancialSubject для LAND_PLOT."""
    coop = Cooperative(name="СТ Ромашка")
    test_db.add(coop)
    await test_db.flush()

    subject_id = uuid.uuid4()
    fs = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=subject_id,
        cooperative_id=coop.id,
    )
    test_db.add(fs)
    await test_db.commit()
    await test_db.refresh(fs)

    assert fs.id is not None
    assert isinstance(fs.id, uuid.UUID)
    assert fs.subject_type == "LAND_PLOT"
    assert fs.subject_id == subject_id
    assert fs.cooperative_id == coop.id
    assert fs.code is not None
    assert fs.code.startswith("FS-")
    assert fs.status == "active"
    assert fs.created_at is not None
    assert isinstance(fs.created_at, datetime)


@pytest.mark.asyncio
async def test_financial_subject_unique_type_subject_coop(test_db: AsyncSession) -> None:
    """Уникальность комбинации (subject_type, subject_id, cooperative_id)."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    subject_id = uuid.uuid4()
    fs1 = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=subject_id,
        cooperative_id=coop.id,
    )
    test_db.add(fs1)
    await test_db.commit()

    fs2 = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=subject_id,
        cooperative_id=coop.id,
    )
    test_db.add(fs2)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_financial_subject_same_subject_different_coop(test_db: AsyncSession) -> None:
    """Один subject_id может быть в разных СТ (разные cooperative_id)."""
    coop1 = Cooperative(name="СТ Первое")
    coop2 = Cooperative(name="СТ Второе")
    test_db.add_all([coop1, coop2])
    await test_db.flush()

    subject_id = uuid.uuid4()
    fs1 = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=subject_id,
        cooperative_id=coop1.id,
    )
    fs2 = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=subject_id,
        cooperative_id=coop2.id,
    )
    test_db.add_all([fs1, fs2])
    await test_db.commit()
    await test_db.refresh(fs1)
    await test_db.refresh(fs2)

    assert fs1.id != fs2.id
    assert fs1.code != fs2.code


@pytest.mark.asyncio
async def test_financial_subject_code_unique(test_db: AsyncSession) -> None:
    """Уникальность code: два FinancialSubject не могут иметь одинаковый code."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    forced_code = "FS-DUPLICATE"
    fs1 = FinancialSubject(
        subject_type="LAND_PLOT",
        subject_id=uuid.uuid4(),
        cooperative_id=coop.id,
        code=forced_code,
    )
    test_db.add(fs1)
    await test_db.commit()

    fs2 = FinancialSubject(
        subject_type="WATER_METER",
        subject_id=uuid.uuid4(),
        cooperative_id=coop.id,
        code=forced_code,
    )
    test_db.add(fs2)
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_financial_subject_subject_types(test_db: AsyncSession) -> None:
    """Все допустимые subject_type сохраняются корректно."""
    coop = Cooperative(name="СТ Тест")
    test_db.add(coop)
    await test_db.flush()

    valid_types = ["LAND_PLOT", "WATER_METER", "ELECTRICITY_METER", "GENERAL_DECISION"]
    for stype in valid_types:
        fs = FinancialSubject(
            subject_type=stype,
            subject_id=uuid.uuid4(),
            cooperative_id=coop.id,
        )
        test_db.add(fs)
    await test_db.commit()

    from sqlalchemy import select

    result = await test_db.execute(
        select(FinancialSubject).where(FinancialSubject.cooperative_id == coop.id)
    )
    subjects = result.scalars().all()
    assert len(subjects) == len(valid_types)
    saved_types = {s.subject_type for s in subjects}
    assert saved_types == set(valid_types)


def test_generate_financial_subject_code() -> None:
    """Генератор code возвращает строку формата FS-XXXXXXXX."""
    code = generate_financial_subject_code()
    assert code.startswith("FS-")
    assert len(code) == 11  # "FS-" + 8 hex chars
    # Uniqueness: two generated codes should differ
    code2 = generate_financial_subject_code()
    assert code != code2
