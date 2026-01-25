from __future__ import annotations

import random
from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.charge_item import ChargeItem
from app.models.doc_accrual import DocAccrual, DocAccrualRow
from app.models.doc_payment import DocPayment, DocPaymentRow
from app.models.owner import Owner
from app.models.plot import Plot
from app.models.plot_owner import PlotOwner
from app.models.snt import Snt
from app.services.posting.accrual import post_accrual
from app.services.posting.payment import post_payment


def _ensure_snt(db, name: str) -> Snt:
    existing = db.execute(select(Snt).where(Snt.name == name)).scalar_one_or_none()
    if existing:
        return existing
    obj = Snt(name=name)
    db.add(obj)
    db.flush()
    return obj


def main() -> None:
    random.seed(42)

    db = SessionLocal()
    try:
        with db.begin():
            snts = [
                _ensure_snt(db, "СНТ Берёзка"),
                _ensure_snt(db, "СНТ Ромашка"),
                _ensure_snt(db, "СНТ Дружба"),
            ]

            for snt in snts:
                # Идемпотентность: если по СНТ уже есть участки/собственники — считаем, что seed уже выполнен.
                has_any_plot = db.execute(select(Plot.id).where(Plot.snt_id == snt.id).limit(1)).first()
                has_any_owner = db.execute(select(Owner.id).where(Owner.snt_id == snt.id).limit(1)).first()
                if has_any_plot or has_any_owner:
                    continue

                owners_count = random.randint(10, 15)
                plots_count = random.randint(10, 15)

                owners: list[Owner] = []
                plots: list[Plot] = []

                for i in range(owners_count):
                    owners.append(Owner(snt_id=snt.id, full_name=f"Член {snt.id}-{i+1}"))
                db.add_all(owners)
                db.flush()

                for i in range(plots_count):
                    plots.append(Plot(snt_id=snt.id, number=str(i + 1)))
                db.add_all(plots)
                db.flush()

                # Связь участок -> собственник (1:1 для простого теста)
                plot_owner_rows: list[PlotOwner] = []
                for i, p in enumerate(plots):
                    o = owners[i % len(owners)]
                    plot_owner_rows.append(
                        PlotOwner(snt_id=snt.id, plot_id=p.id, owner_id=o.id, date_from=date(2020, 1, 1), date_to=None)
                    )
                db.add_all(plot_owner_rows)

                # Статьи
                items = [
                    ChargeItem(snt_id=snt.id, name="Членский взнос", type="membership"),
                    ChargeItem(snt_id=snt.id, name="Целевой взнос", type="target"),
                    ChargeItem(snt_id=snt.id, name="Электроэнергия", type="service"),
                ]
                db.add_all(items)
                db.flush()

        # Документы + проведение (отдельно, чтобы наглядно показать механику)
        with db.begin():
            for snt in db.execute(select(Snt).order_by(Snt.id)).scalars().all():
                existing_accrual = db.execute(
                    select(DocAccrual.id).where(DocAccrual.snt_id == snt.id, DocAccrual.number == f"A-{snt.id}-1")
                ).first()
                existing_payment = db.execute(
                    select(DocPayment.id).where(DocPayment.snt_id == snt.id, DocPayment.number == f"P-{snt.id}-1")
                ).first()
                if existing_accrual or existing_payment:
                    continue

                owners = db.execute(select(Owner).where(Owner.snt_id == snt.id).order_by(Owner.id)).scalars().all()
                plots = db.execute(select(Plot).where(Plot.snt_id == snt.id).order_by(Plot.id)).scalars().all()
                items = (
                    db.execute(select(ChargeItem).where(ChargeItem.snt_id == snt.id).order_by(ChargeItem.id))
                    .scalars()
                    .all()
                )

                # Начисление: по всем участкам членский взнос
                accrual = DocAccrual(snt_id=snt.id, number=f"A-{snt.id}-1", date=date(2026, 1, 1), is_posted=False)
                db.add(accrual)
                db.flush()

                accrual_rows = []
                for p in plots:
                    o = owners[(p.id - plots[0].id) % len(owners)]
                    accrual_rows.append(
                        DocAccrualRow(
                            snt_id=snt.id,
                            doc_id=accrual.id,
                            plot_id=p.id,
                            owner_id=o.id,
                            charge_item_id=items[0].id,
                            amount=1500,
                            period_from=date(2026, 1, 1),
                            period_to=date(2026, 1, 31),
                        )
                    )
                db.add_all(accrual_rows)

                # Оплата: частичная (первые 5 участков)
                payment = DocPayment(snt_id=snt.id, number=f"P-{snt.id}-1", date=date(2026, 1, 10), is_posted=False)
                db.add(payment)
                db.flush()

                payment_rows = []
                for p in plots[:5]:
                    o = owners[(p.id - plots[0].id) % len(owners)]
                    payment_rows.append(
                        DocPaymentRow(
                            snt_id=snt.id,
                            doc_id=payment.id,
                            plot_id=p.id,
                            owner_id=o.id,
                            charge_item_id=items[0].id,
                            amount=1000,
                        )
                    )
                db.add_all(payment_rows)

        # Проведение по алгоритму пересчёта движений
        for snt in db.execute(select(Snt).order_by(Snt.id)).scalars().all():
            accrual = (
                db.execute(select(DocAccrual).where(DocAccrual.snt_id == snt.id).order_by(DocAccrual.id.desc()))
                .scalars()
                .first()
            )
            payment = (
                db.execute(select(DocPayment).where(DocPayment.snt_id == snt.id).order_by(DocPayment.id.desc()))
                .scalars()
                .first()
            )
            if accrual:
                post_accrual(db, snt_id=snt.id, doc_id=accrual.id)
            if payment:
                post_payment(db, snt_id=snt.id, doc_id=payment.id)

        print("Seed completed: created 3 SNTs with members/plots, documents and posted movements.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

