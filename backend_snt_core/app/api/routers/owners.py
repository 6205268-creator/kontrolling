from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.owner import Owner
from app.schemas.refs import OwnerCreate, OwnerRead

router = APIRouter(prefix="/snts/{snt_id}/owners")


@router.post("", response_model=OwnerRead)
def create_owner(snt_id: int, payload: OwnerCreate, db: Session = Depends(get_db)) -> OwnerRead:
    with db.begin():
        obj = Owner(snt_id=snt_id, full_name=payload.full_name)
        db.add(obj)
        db.flush()
        return OwnerRead(id=obj.id, snt_id=obj.snt_id, full_name=obj.full_name)


@router.get("", response_model=list[OwnerRead])
def list_owners(snt_id: int, db: Session = Depends(get_db)) -> list[OwnerRead]:
    items = (
        db.execute(select(Owner).where(Owner.snt_id == snt_id).order_by(Owner.id))
        .scalars()
        .all()
    )
    return [OwnerRead(id=i.id, snt_id=i.snt_id, full_name=i.full_name) for i in items]

