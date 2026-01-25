from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.plot import Plot
from app.schemas.refs import PlotCreate, PlotRead

router = APIRouter(prefix="/snts/{snt_id}/plots")


@router.post("", response_model=PlotRead)
def create_plot(snt_id: int, payload: PlotCreate, db: Session = Depends(get_db)) -> PlotRead:
    with db.begin():
        obj = Plot(snt_id=snt_id, number=payload.number)
        db.add(obj)
        db.flush()
        return PlotRead(id=obj.id, snt_id=obj.snt_id, number=obj.number)


@router.get("", response_model=list[PlotRead])
def list_plots(snt_id: int, db: Session = Depends(get_db)) -> list[PlotRead]:
    items = (
        db.execute(select(Plot).where(Plot.snt_id == snt_id).order_by(Plot.id))
        .scalars()
        .all()
    )
    return [PlotRead(id=i.id, snt_id=i.snt_id, number=i.number) for i in items]

