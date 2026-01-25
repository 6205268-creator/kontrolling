"""API v2: auth via X-User-Id, strict isolation for snt_user."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.app_user import AppUser
from app.models.meter import Meter
from app.models.physical_person import PhysicalPerson
from app.models.plot import Plot
from app.models.plot_owner import PlotOwner
from app.models.snt import Snt
from app.models.snt_member import SntMember
from app.schemas.v2 import (
    AppUserRead,
    MeterRead,
    PhysicalPersonDetailRead,
    PhysicalPersonRead,
    PlotOwnerRead,
    PlotRead,
    SntMemberRead,
    SntRead,
)

router = APIRouter()


def _allowed_snt_id(user: AppUser, snt_id: int | None) -> int | None:
    """For snt_user, only their snt_id is allowed. Admin: any."""
    if user.role == "admin":
        return snt_id
    return user.snt_id


@router.get("/users", response_model=list[AppUserRead])
def list_users(db: Session = Depends(get_db)) -> list[AppUserRead]:
    """List all users (for login dropdown). No auth filtering."""
    rows = db.execute(select(AppUser).order_by(AppUser.id)).scalars().all()
    return [AppUserRead(id=r.id, name=r.name, role=r.role, snt_id=r.snt_id) for r in rows]


@router.get("/me", response_model=AppUserRead)
def me(user: AppUser = Depends(get_current_user)) -> AppUserRead:
    """Current user info (role, snt_id). Frontend uses this to show/hide SNT switcher."""
    return AppUserRead(id=user.id, name=user.name, role=user.role, snt_id=user.snt_id)


@router.get("/snts", response_model=list[SntRead])
def list_snts(
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> list[SntRead]:
    """Admin: all SNTs. snt_user: only their SNT. Strict isolation."""
    if user.role == "snt_user":
        if not user.snt_id:
            return []
        snts = db.execute(select(Snt).where(Snt.id == user.snt_id)).scalars().all()
    else:
        snts = db.execute(select(Snt).order_by(Snt.id)).scalars().all()
    return [SntRead(id=s.id, name=s.name) for s in snts]


@router.get("/physical-persons", response_model=list[PhysicalPersonRead])
def list_physical_persons(
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> list[PhysicalPersonRead]:
    """Admin: all. snt_user: only persons linked to their SNT (member or plot_owner)."""
    if user.role == "snt_user" and user.snt_id:
        member_ids = db.execute(
            select(SntMember.physical_person_id).where(SntMember.snt_id == user.snt_id)
        ).scalars().all()
        owner_ids = db.execute(
            select(PlotOwner.physical_person_id).where(PlotOwner.snt_id == user.snt_id)
        ).scalars().all()
        allowed_ids = {x for sub in (member_ids, owner_ids) for x in sub}
        if not allowed_ids:
            return []
        rows = db.execute(
            select(PhysicalPerson).where(PhysicalPerson.id.in_(allowed_ids)).order_by(PhysicalPerson.id)
        ).scalars().all()
    else:
        rows = db.execute(select(PhysicalPerson).order_by(PhysicalPerson.id)).scalars().all()
    return [PhysicalPersonRead(id=r.id, full_name=r.full_name, inn=r.inn, phone=r.phone) for r in rows]


@router.get("/physical-persons/{person_id}", response_model=PhysicalPersonDetailRead)
def get_physical_person(
    person_id: int,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> PhysicalPersonDetailRead:
    """Admin: any. snt_user: 404 if person not linked to their SNT."""
    person = db.execute(select(PhysicalPerson).where(PhysicalPerson.id == person_id)).scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Physical person not found")

    if user.role == "snt_user" and user.snt_id:
        has_member = db.execute(
            select(SntMember.id).where(
                SntMember.physical_person_id == person_id,
                SntMember.snt_id == user.snt_id,
            ).limit(1)
        ).first()
        has_owner = db.execute(
            select(PlotOwner.id).where(
                PlotOwner.physical_person_id == person_id,
                PlotOwner.snt_id == user.snt_id,
            ).limit(1)
        ).first()
        if not has_member and not has_owner:
            raise HTTPException(status_code=404, detail="Physical person not found")

    members_q = (
        select(SntMember, Snt.name)
        .join(Snt, Snt.id == SntMember.snt_id)
        .where(SntMember.physical_person_id == person_id)
    )
    if user.role == "snt_user" and user.snt_id:
        members_q = members_q.where(SntMember.snt_id == user.snt_id)
    members = db.execute(members_q.order_by(SntMember.date_from.desc())).all()

    po_q = (
        select(PlotOwner, Plot.number, Snt.name)
        .join(Plot, Plot.id == PlotOwner.plot_id)
        .join(Snt, Snt.id == PlotOwner.snt_id)
        .where(PlotOwner.physical_person_id == person_id)
    )
    if user.role == "snt_user" and user.snt_id:
        po_q = po_q.where(PlotOwner.snt_id == user.snt_id)
    plot_owners_raw = db.execute(po_q.order_by(PlotOwner.date_from.desc())).all()

    return PhysicalPersonDetailRead(
        id=person.id,
        full_name=person.full_name,
        inn=person.inn,
        phone=person.phone,
        members=[
            SntMemberRead(
                id=m.id,
                snt_id=m.snt_id,
                physical_person_id=m.physical_person_id,
                date_from=m.date_from,
                date_to=m.date_to,
                snt_name=snt_name,
                physical_person_name=person.full_name,
            )
            for (m, snt_name) in members
        ],
        plot_owners=[
            PlotOwnerRead(
                id=po.id,
                snt_id=po.snt_id,
                plot_id=po.plot_id,
                physical_person_id=po.physical_person_id,
                date_from=po.date_from,
                date_to=po.date_to,
                plot_number=num,
                snt_name=snt_name,
            )
            for (po, num, snt_name) in plot_owners_raw
        ],
    )


@router.get("/snt-members", response_model=list[SntMemberRead])
def list_snt_members(
    snt_id: int | None = Query(None, description="Filter by SNT (admin only)"),
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> list[SntMemberRead]:
    """snt_user: only their SNT, snt_id ignored. Admin: use snt_id param."""
    effective_snt = _allowed_snt_id(user, snt_id)
    if effective_snt is None:
        return []
    rows = (
        db.execute(
            select(SntMember, Snt.name, PhysicalPerson.full_name)
            .join(Snt, Snt.id == SntMember.snt_id)
            .join(PhysicalPerson, PhysicalPerson.id == SntMember.physical_person_id)
            .where(SntMember.snt_id == effective_snt)
            .order_by(SntMember.date_from.desc())
        )
    ).all()
    return [
        SntMemberRead(
            id=m.id,
            snt_id=m.snt_id,
            physical_person_id=m.physical_person_id,
            date_from=m.date_from,
            date_to=m.date_to,
            snt_name=snt_name,
            physical_person_name=pp_name,
        )
        for (m, snt_name, pp_name) in rows
    ]


@router.get("/plots", response_model=list[PlotRead])
def list_plots(
    snt_id: int | None = Query(None, description="Filter by SNT (admin only)"),
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> list[PlotRead]:
    """snt_user: only their SNT. Admin: use snt_id param."""
    effective_snt = _allowed_snt_id(user, snt_id)
    if effective_snt is None:
        return []
    rows = (
        db.execute(
            select(Plot, Snt.name)
            .join(Snt, Snt.id == Plot.snt_id)
            .where(Plot.snt_id == effective_snt)
            .order_by(Plot.number)
        )
    ).all()
    return [PlotRead(id=p.id, snt_id=p.snt_id, number=p.number, snt_name=snt_name) for (p, snt_name) in rows]


@router.get("/meters", response_model=list[MeterRead])
def list_meters(
    snt_id: int | None = Query(None, description="Filter by SNT (admin only)"),
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> list[MeterRead]:
    """snt_user: only their SNT. Admin: use snt_id param."""
    effective_snt = _allowed_snt_id(user, snt_id)
    if effective_snt is None:
        return []
    rows = (
        db.execute(
            select(Meter, Plot.number, Snt.name)
            .join(Plot, Plot.id == Meter.plot_id)
            .join(Snt, Snt.id == Meter.snt_id)
            .where(Meter.snt_id == effective_snt)
            .order_by(Meter.plot_id, Meter.meter_type)
        )
    ).all()
    return [
        MeterRead(
            id=m.id,
            snt_id=m.snt_id,
            plot_id=m.plot_id,
            meter_type=m.meter_type,
            serial_number=m.serial_number,
            plot_number=num,
            snt_name=snt_name,
        )
        for (m, num, snt_name) in rows
    ]
