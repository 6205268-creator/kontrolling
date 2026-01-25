from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.snt import Snt
from app.schemas.refs import SntCreate, SntRead

router = APIRouter(prefix="/snts")


@router.post("", response_model=SntRead)
def create_snt(payload: SntCreate, db: Session = Depends(get_db)) -> SntRead:
    with db.begin():
        obj = Snt(name=payload.name)
        db.add(obj)
        db.flush()
        return SntRead(id=obj.id, name=obj.name)


@router.get("", response_model=list[SntRead])
def list_snts(db: Session = Depends(get_db)) -> list[SntRead]:
    items = db.execute(select(Snt).order_by(Snt.id)).scalars().all()
    return [SntRead(id=i.id, name=i.name) for i in items]

