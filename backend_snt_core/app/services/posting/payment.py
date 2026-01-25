from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.doc_payment import DocPayment, DocPaymentRow
from app.models.reg_balance import RegBalance


def post_payment(db: Session, *, snt_id: int, doc_id: int) -> None:
    """Проведение документа оплаты (строго по алгоритму пересчёта движений)."""
    with db.begin():
        db.execute(
            delete(RegBalance).where(
                RegBalance.snt_id == snt_id,
                RegBalance.doc_payment_id == doc_id,
            )
        )

        doc = db.execute(
            select(DocPayment).where(DocPayment.snt_id == snt_id, DocPayment.id == doc_id)
        ).scalar_one()

        rows = (
            db.execute(
                select(DocPaymentRow).where(DocPaymentRow.snt_id == snt_id, DocPaymentRow.doc_id == doc_id)
            )
            .scalars()
            .all()
        )

        movements: list[RegBalance] = []
        for r in rows:
            movements.append(
                RegBalance(
                    snt_id=snt_id,
                    doc_accrual_id=None,
                    doc_accrual_row_id=None,
                    doc_payment_id=doc_id,
                    doc_payment_row_id=r.id,
                    date=doc.date,
                    plot_id=r.plot_id,
                    owner_id=r.owner_id,
                    charge_item_id=r.charge_item_id,
                    amount_debit=0,
                    amount_credit=r.amount,
                )
            )

        db.add_all(movements)

        db.execute(
            update(DocPayment)
            .where(DocPayment.snt_id == snt_id, DocPayment.id == doc_id)
            .values(is_posted=True)
        )


def unpost_payment(db: Session, *, snt_id: int, doc_id: int) -> None:
    """Отмена проведения документа оплаты (строго по алгоритму)."""
    with db.begin():
        db.execute(
            delete(RegBalance).where(
                RegBalance.snt_id == snt_id,
                RegBalance.doc_payment_id == doc_id,
            )
        )
        db.execute(
            update(DocPayment)
            .where(DocPayment.snt_id == snt_id, DocPayment.id == doc_id)
            .values(is_posted=False)
        )

