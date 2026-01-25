from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.doc_accrual import DocAccrual, DocAccrualRow
from app.schemas.documents import AccrualCreate, AccrualRead
from app.services.posting.accrual import post_accrual, unpost_accrual

router = APIRouter(prefix="/snts/{snt_id}/documents/accruals")


@router.post("", response_model=AccrualRead)
def create_accrual(snt_id: int, payload: AccrualCreate, db: Session = Depends(get_db)) -> AccrualRead:
    with db.begin():
        doc = DocAccrual(snt_id=snt_id, number=payload.number, date=payload.date, is_posted=False)
        db.add(doc)
        db.flush()

        rows = [
            DocAccrualRow(
                snt_id=snt_id,
                doc_id=doc.id,
                plot_id=r.plot_id,
                owner_id=r.owner_id,
                charge_item_id=r.charge_item_id,
                period_from=r.period_from,
                period_to=r.period_to,
                amount=r.amount,
            )
            for r in payload.rows
        ]
        db.add_all(rows)

        return AccrualRead(
            id=doc.id, snt_id=doc.snt_id, number=doc.number, date=doc.date, is_posted=doc.is_posted
        )


@router.get("", response_model=list[AccrualRead])
def list_accruals(snt_id: int, db: Session = Depends(get_db)) -> list[AccrualRead]:
    docs = (
        db.execute(select(DocAccrual).where(DocAccrual.snt_id == snt_id).order_by(DocAccrual.id))
        .scalars()
        .all()
    )
    return [
        AccrualRead(id=d.id, snt_id=d.snt_id, number=d.number, date=d.date, is_posted=d.is_posted)
        for d in docs
    ]


@router.post("/{doc_id}/post")
def post_document(snt_id: int, doc_id: int, db: Session = Depends(get_db)) -> dict:
    post_accrual(db, snt_id=snt_id, doc_id=doc_id)
    return {"status": "posted"}


@router.post("/{doc_id}/unpost")
def unpost_document(snt_id: int, doc_id: int, db: Session = Depends(get_db)) -> dict:
    unpost_accrual(db, snt_id=snt_id, doc_id=doc_id)
    return {"status": "unposted"}

