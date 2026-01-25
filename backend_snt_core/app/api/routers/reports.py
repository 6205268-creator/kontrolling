from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.reg_balance import RegBalance

router = APIRouter(prefix="/snts/{snt_id}/reports")


@router.get("/balance")
def report_balance(
    snt_id: int,
    on_date: date = Query(..., description="Дата, на которую строится сальдо"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Простое сальдо на дату: сумма дебет - кредит по регистру `reg_balance`.
    """
    q = (
        select(
            RegBalance.plot_id,
            RegBalance.owner_id,
            RegBalance.charge_item_id,
            func.sum(RegBalance.amount_debit - RegBalance.amount_credit).label("balance"),
        )
        .where(RegBalance.snt_id == snt_id, RegBalance.date <= on_date)
        .group_by(RegBalance.plot_id, RegBalance.owner_id, RegBalance.charge_item_id)
        .order_by(RegBalance.plot_id, RegBalance.owner_id, RegBalance.charge_item_id)
    )

    rows = db.execute(q).all()
    return [
        {
            "plot_id": r.plot_id,
            "owner_id": r.owner_id,
            "charge_item_id": r.charge_item_id,
            "balance": float(r.balance or 0),
        }
        for r in rows
    ]

