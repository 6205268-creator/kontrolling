"""Seed test data for v2: physical persons, SNTs, members, plots, plot_owners, meters, users."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.app_user import AppUser
from app.models.meter import Meter
from app.models.physical_person import PhysicalPerson
from app.models.plot import Plot
from app.models.plot_owner import PlotOwner
from app.models.snt import Snt
from app.models.snt_member import SntMember


def _ensure_snt(db, name: str) -> Snt:
    existing = db.execute(select(Snt).where(Snt.name == name)).scalar_one_or_none()
    if existing:
        return existing
    obj = Snt(name=name)
    db.add(obj)
    db.flush()
    return obj


def _ensure_person(db, full_name: str, phone: str | None = None, inn: str | None = None) -> PhysicalPerson:
    existing = db.execute(select(PhysicalPerson).where(PhysicalPerson.full_name == full_name)).scalar_one_or_none()
    if existing:
        return existing
    obj = PhysicalPerson(full_name=full_name, phone=phone, inn=inn)
    db.add(obj)
    db.flush()
    return obj


def main() -> None:
    db = SessionLocal()
    try:
        with db.begin():
            snts = [
                _ensure_snt(db, "СНТ «Солнечный»"),
                _ensure_snt(db, "СНТ «Берёзовая роща»"),
                _ensure_snt(db, "СНТ «Рассвет»"),
            ]
            db.flush()

            persons = [
                _ensure_person(db, "Иванов Иван Иванович", "+7 (900) 123-45-67"),
                _ensure_person(db, "Петрова Мария Сергеевна", "+7 (900) 234-56-78"),
                _ensure_person(db, "Сидоров Алексей Владимирович", "+7 (900) 345-67-89"),
                _ensure_person(db, "Козлова Елена Николаевна", "+7 (900) 456-78-90"),
                _ensure_person(db, "Морозов Дмитрий Андреевич", "+7 (900) 567-89-01"),
                _ensure_person(db, "Новикова Ольга Петровна", "+7 (900) 678-90-12"),
                _ensure_person(db, "Волков Константин Сергеевич", "+7 (900) 789-01-23"),
                _ensure_person(db, "Соколова Татьяна Викторовна", "+7 (900) 890-12-34"),
            ]
            db.flush()

            has_members = db.execute(select(SntMember.id).limit(1)).first()
            if not has_members:
                sun, birch, dawn = snts[0], snts[1], snts[2]
                for s, count in [(sun, 5), (birch, 4), (dawn, 3)]:
                    for i in range(1, count + 1):
                        db.add(Plot(snt_id=s.id, number=str(i)))
                db.flush()

                plots_sun = db.execute(select(Plot).where(Plot.snt_id == sun.id).order_by(Plot.id)).scalars().all()
                plots_birch = db.execute(select(Plot).where(Plot.snt_id == birch.id).order_by(Plot.id)).scalars().all()
                plots_dawn = db.execute(select(Plot).where(Plot.snt_id == dawn.id).order_by(Plot.id)).scalars().all()
                d0 = date(2020, 1, 1)

                memberships = [
                    (sun.id, persons[0].id, d0, None),
                    (sun.id, persons[1].id, d0, None),
                    (sun.id, persons[2].id, d0, None),
                    (sun.id, persons[3].id, d0, None),
                    (sun.id, persons[4].id, d0, None),
                    (sun.id, persons[5].id, d0, None),
                    (sun.id, persons[6].id, d0, None),
                    (sun.id, persons[7].id, d0, None),
                    (birch.id, persons[2].id, d0, None),
                    (birch.id, persons[3].id, d0, None),
                    (birch.id, persons[4].id, d0, None),
                    (dawn.id, persons[5].id, d0, None),
                    (dawn.id, persons[6].id, d0, None),
                ]
                for snt_id, pp_id, df, dt in memberships:
                    db.add(SntMember(snt_id=snt_id, physical_person_id=pp_id, date_from=df, date_to=dt))
                db.flush()

                plot_owners_data = [
                    (sun.id, plots_sun[0].id, persons[0].id, d0, None),
                    (sun.id, plots_sun[1].id, persons[1].id, d0, None),
                    (sun.id, plots_sun[2].id, persons[2].id, d0, None),
                    (sun.id, plots_sun[3].id, persons[3].id, d0, None),
                    (sun.id, plots_sun[4].id, persons[4].id, d0, None),
                    (birch.id, plots_birch[0].id, persons[2].id, d0, None),
                    (birch.id, plots_birch[1].id, persons[3].id, d0, None),
                    (birch.id, plots_birch[2].id, persons[4].id, d0, None),
                    (dawn.id, plots_dawn[0].id, persons[5].id, d0, None),
                    (dawn.id, plots_dawn[1].id, persons[6].id, d0, None),
                ]
                for snt_id, plot_id, pp_id, df, dt in plot_owners_data:
                    db.add(PlotOwner(snt_id=snt_id, plot_id=plot_id, physical_person_id=pp_id, date_from=df, date_to=dt))
                db.flush()

            has_users = db.execute(select(AppUser.id).limit(1)).first()
            if not has_users:
                db.add(AppUser(name="Администратор", role="admin", snt_id=None))
                db.flush()
                for s in snts:
                    db.add(AppUser(name=s.name, role="snt_user", snt_id=s.id))
                db.flush()

            has_meters = db.execute(select(Meter.id).limit(1)).first()
            if not has_meters:
                plots = db.execute(select(Plot).order_by(Plot.snt_id, Plot.id)).scalars().all()
                for idx, p in enumerate(plots):
                    db.add(Meter(snt_id=p.snt_id, plot_id=p.id, meter_type="water", serial_number=f"W-{p.snt_id}-{p.number}"))
                    db.add(Meter(snt_id=p.snt_id, plot_id=p.id, meter_type="electricity", serial_number=f"E-{p.snt_id}-{p.number}"))
                db.flush()

        print("Seed v2 completed: SNTs, persons, members, plots, plot_owners, users, meters.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
