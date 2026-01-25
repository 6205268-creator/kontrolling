from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.doc_payment import DocPayment, DocPaymentRow
from app.schemas.documents import PaymentCreate, PaymentRead
from app.services.posting.payment import post_payment, unpost_payment

router = APIRouter(prefix="/snts/{snt_id}/documents/payments")


@router.post("", response_model=PaymentRead)
def create_payment(snt_id: int, payload: PaymentCreate, db: Session = Depends(get_db)) -> PaymentRead:
    with db.begin():
        doc = DocPayment(snt_id=snt_id, number=payload.number, date=payload.date, is_posted=False)
        db.add(doc)
        db.flush()

        rows = [
            DocPaymentRow(
                snt_id=snt_id,
                doc_id=doc.id,
                plot_id=r.plot_id,
                owner_id=r.owner_id,
                charge_item_id=r.charge_item_id,
                amount=r.amount,
            )
            for r in payload.rows
        ]
        db.add_all(rows)

        return PaymentRead(
            id=doc.id, snt_id=doc.snt_id, number=doc.number, date=doc.date, is_posted=doc.is_posted
        )


@router.get("", response_model=list[PaymentRead])
def list_payments(snt_id: int, db: Session = Depends(get_db)) -> list[PaymentRead]:
    docs = (
        db.execute(select(DocPayment).where(DocPayment.snt_id == snt_id).order_by(DocPayment.id))
        .scalars()
        .all()
    )
    return [
        PaymentRead(id=d.id, snt_id=d.snt_id, number=d.number, date=d.date, is_posted=d.is_posted)
        for d in docs
    ]


@router.post("/{doc_id}/post")
def post_document(snt_id: int, doc_id: int, db: Session = Depends(get_db)) -> dict:
    post_payment(db, snt_id=snt_id, doc_id=doc_id)
    return {"status": "posted"}


@router.post("/{doc_id}/unpost")
def unpost_document(snt_id: int, doc_id: int, db: Session = Depends(get_db)) -> dict:
    unpost_payment(db, snt_id=snt_id, doc_id=doc_id)
    return {"status": "unposted"}

