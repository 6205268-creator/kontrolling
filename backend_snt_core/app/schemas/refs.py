from pydantic import BaseModel


class SntCreate(BaseModel):
    name: str


class SntRead(BaseModel):
    id: int
    name: str


class PlotCreate(BaseModel):
    number: str


class PlotRead(BaseModel):
    id: int
    snt_id: int
    number: str


class OwnerCreate(BaseModel):
    full_name: str


class OwnerRead(BaseModel):
    id: int
    snt_id: int
    full_name: str


class ChargeItemCreate(BaseModel):
    name: str
    type: str


class ChargeItemRead(BaseModel):
    id: int
    snt_id: int
    name: str
    type: str

