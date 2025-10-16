from __future__ import annotations

from datetime import date

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import HttpUrl


#
# class CRSProperties(BaseModel):
#     name: str
#
#
# class CRS(BaseModel):
#     type: str
#     properties: CRSProperties
#
#
# class Geometrie(BaseModel):
#     type: str
#     crs: CRS
#     coordinates: List[Any]  # Could be refined to List[List[List[List[float]]]] for strict typing
#
#
# class Provincie(BaseModel):
#     niscode: str
#     naam: str
#
#
# class Gemeente(BaseModel):
#     niscode: str
#     naam: str
#
#
# class LocatieElement(BaseModel):
#     id: int
#     type: HttpUrl
#     provincie: Provincie
#     gemeente: Gemeente
#
#
# class Label(BaseModel):
#     label: str
#     type: str
#     language: str
#
#
# class Plantype(BaseModel):
#     uri: HttpUrl
#     label: Label
#
#
# class Actor(BaseModel):
#     uri: HttpUrl
#     description: str
#
#
# class SystemFields(BaseModel):
#     created_at: datetime
#     created_by: Actor
#     updated_at: datetime
#     updated_by: Actor
#
#
# class Status(BaseModel):
#     id: int
#     status_id: int
#     naam: str
#     datum: datetime
#     aanpasser_uri: HttpUrl
#     aanpasser_omschrijving: str
#     opmerkingen: Optional[str] = None
#     actief: bool

class PlanBase(BaseModel):
    onderwerp: str | None
    datum_goedkeuring: date | None
    startdatum: date | None
    einddatum: date | None
    datum_goedkeuring: date | None
    beheerscommissie: bool | None
    # geometrie: Geometrie
    # locatie_elementen: List[LocatieElement]
    # bestanden: List[Any]
    # erfgoedobjecten: List[Any]
    # plantype: Plantype
    # relaties: List[Any]
    # systemfields: SystemFields
    # actief: bool
    # status: Status
    # statussen: List[Status]


class PlanCreate(PlanBase):
    """Schema for creating an Plan."""
    pass


class PlanUpdate(PlanBase):
    """Schema for updating an Plan."""
    pass


class PlanResponse(PlanBase):
    """Schema for Plan response."""
    id: int

    model_config = ConfigDict(from_attributes=True)
