from datetime import date

from pydantic import BaseModel


class SntRead(BaseModel):
    id: int
    name: str


class PhysicalPersonRead(BaseModel):
    id: int
    full_name: str
    inn: str | None
    phone: str | None


class SntMemberRead(BaseModel):
    id: int
    snt_id: int
    physical_person_id: int
    date_from: date
    date_to: date | None
    snt_name: str | None = None
    physical_person_name: str | None = None


class PlotRead(BaseModel):
    id: int
    snt_id: int
    number: str
    snt_name: str | None = None


class PlotOwnerRead(BaseModel):
    id: int
    snt_id: int
    plot_id: int
    physical_person_id: int
    date_from: date
    date_to: date | None
    plot_number: str | None = None
    snt_name: str | None = None


class PhysicalPersonDetailRead(PhysicalPersonRead):
    members: list[SntMemberRead] = []
    plot_owners: list[PlotOwnerRead] = []


class AppUserRead(BaseModel):
    id: int
    name: str
    role: str
    snt_id: int | None = None


class MeterRead(BaseModel):
    id: int
    snt_id: int
    plot_id: int
    meter_type: str
    serial_number: str | None = None
    plot_number: str | None = None
    snt_name: str | None = None
