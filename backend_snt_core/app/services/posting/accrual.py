from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.doc_accrual import DocAccrual, DocAccrualRow
from app.models.reg_balance import RegBalance


def post_accrual(db: Session, *, snt_id: int, doc_id: int) -> None:
    """
    Проведение документа начисления.

    Алгоритм строго:
    1) BEGIN
    2) DELETE старых движений по doc_id
    3) INSERT новых движений на основе строк документа
    4) UPDATE is_posted=true
    5) COMMIT
    """
    with db.begin():
        db.execute(
            delete(RegBalance).where(
                RegBalance.snt_id == snt_id,
                RegBalance.doc_accrual_id == doc_id,
            )
        )

        doc = db.execute(
            select(DocAccrual).where(DocAccrual.snt_id == snt_id, DocAccrual.id == doc_id)
        ).scalar_one()

        rows = (
            db.execute(
                select(DocAccrualRow).where(DocAccrualRow.snt_id == snt_id, DocAccrualRow.doc_id == doc_id)
            )
            .scalars()
            .all()
        )

        movements: list[RegBalance] = []
        for r in rows:
            movements.append(
                RegBalance(
                    snt_id=snt_id,
                    doc_accrual_id=doc_id,
                    doc_accrual_row_id=r.id,
                    doc_payment_id=None,
                    doc_payment_row_id=None,
                    date=doc.date,
                    plot_id=r.plot_id,
                    owner_id=r.owner_id,
                    charge_item_id=r.charge_item_id,
                    amount_debit=r.amount,
                    amount_credit=0,
                )
            )

        db.add_all(movements)

        db.execute(
            update(DocAccrual)
            .where(DocAccrual.snt_id == snt_id, DocAccrual.id == doc_id)
            .values(is_posted=True)
        )


def unpost_accrual(db: Session, *, snt_id: int, doc_id: int) -> None:
    """
    Отмена проведения документа начисления.

    Алгоритм строго:
    1) BEGIN
    2) DELETE движений по doc_id
    3) UPDATE is_posted=false
    4) COMMIT
    """
    with db.begin():
        db.execute(
            delete(RegBalance).where(
                RegBalance.snt_id == snt_id,
                RegBalance.doc_accrual_id == doc_id,
            )
        )
        db.execute(
            update(DocAccrual)
            .where(DocAccrual.snt_id == snt_id, DocAccrual.id == doc_id)
            .values(is_posted=False)
        )

