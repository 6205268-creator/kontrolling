from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.charge_item import ChargeItem
from app.schemas.refs import ChargeItemCreate, ChargeItemRead

router = APIRouter(prefix="/snts/{snt_id}/charge-items")


@router.post("", response_model=ChargeItemRead)
def create_charge_item(
    snt_id: int, payload: ChargeItemCreate, db: Session = Depends(get_db)
) -> ChargeItemRead:
    with db.begin():
        obj = ChargeItem(snt_id=snt_id, name=payload.name, type=payload.type)
        db.add(obj)
        db.flush()
        return ChargeItemRead(id=obj.id, snt_id=obj.snt_id, name=obj.name, type=obj.type)


@router.get("", response_model=list[ChargeItemRead])
def list_charge_items(snt_id: int, db: Session = Depends(get_db)) -> list[ChargeItemRead]:
    items = (
        db.execute(select(ChargeItem).where(ChargeItem.snt_id == snt_id).order_by(ChargeItem.id))
        .scalars()
        .all()
    )
    return [ChargeItemRead(id=i.id, snt_id=i.snt_id, name=i.name, type=i.type) for i in items]

