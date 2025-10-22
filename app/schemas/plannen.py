from __future__ import annotations

from datetime import date
from datetime import datetime
from typing import Annotated
from typing import List
from typing import Optional

from minio.error import MinioException
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import HttpUrl
from pydantic import computed_field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo

from app.models.enums import Bestandssoort
from app.models.enums import Status


class CRSProperties(BaseModel):
    name: str


class CRS(BaseModel):
    type: str
    properties: CRSProperties


class Geometrie(BaseModel):
    type: str
    crs: CRS
    coordinates: Annotated[
        list[list[list[list[float]]]], Field(max_length=2, min_length=1)
    ]


class Provincie(BaseModel):
    niscode: str
    naam: str


class Gemeente(BaseModel):
    niscode: str
    naam: str


class LocatieElementBase(BaseModel):
    type: HttpUrl
    provincie: Provincie
    gemeente: Gemeente


class LocatiElementCreate(LocatieElementBase):
    pass


class LocatieElementResponse(LocatieElementBase):
    id: int


class BestandBase(BaseModel):
    bestandssoort_id: int
    plan_id: int
    naam: str
    mime: str


class BestandCreate(BaseModel):
    naam : Annotated[str, Field(min_length=1)]
    bestandssoort_id : int
    temporary_storage_key: Annotated[str, Field(min_length=1)]
    mime: str

    @field_validator("bestandssoort_id", mode="before")
    @classmethod
    def bestandssoort_id_validator(cls, value: str) -> str:
        Bestandssoort.from_id(value)
        return value

    @model_validator(mode="before")
    def temp_key_validator(self, info: ValidationInfo):
        storage_provider = info.context.get('storageprovider')
        content_manager = info.context.get('content_manager')
        try:
            metadata = storage_provider.get_object_metadata(
                container_key=content_manager.temp_container,
                object_key=self["temporary_storage_key"],
                system_token=content_manager.system_token(),
            )
        except MinioException as me:
            raise ValueError(repr(me))

        self["mime"] = metadata.get('Content-Type', 'application/octet-stream')

        return self

    @field_validator("naam", mode="before")
    @classmethod
    def validate_naam(cls, naam):
        allowed_extensions = (".pdf", ".jpg", ".jpeg", ".png", ".xls", ".xlsx")
        naam_lower = naam.lower()
        if not any(naam_lower.endswith(extension) for extension in allowed_extensions):
            message = (
                "Dit is geen geldige bijlage. De toegelaten bijlagetypes zijn "
                ".pdf, .jp(e)g, .png, .xls(x)"
            )
            raise ValueError(message)
        return naam


class BestandResponse(BestandBase):
    id: int


class Label(BaseModel):
    label: Optional[str] = None
    type: Optional[str] = None
    language: Optional[str] = None


class PlantypeBase(BaseModel):
    uri: HttpUrl
    label: Optional[Label] = None


class PlantypeCreate(PlantypeBase):
    pass


class PlantypeResponse(PlantypeBase):
    pass


class RelatieTypeBase(BaseModel):
    id: str
    type: str
    inverse: str


class RelatieTypeCreate(RelatieTypeBase):
    pass


class RelatieTypeResponse(RelatieTypeBase):
    pass


class RelatieBase(BaseModel):
    type: RelatieTypeBase
    id: int


class RelatieCreate(RelatieBase):
    pass


class RelatieResponse(RelatieBase):
    pass


class SystemFields(BaseModel):
    created_at: datetime
    updated_at: datetime


class StatusType(BaseModel):
    id: int
    naam: str


class StatusBase(BaseModel):
    status_id: int
    naam: str
    datum: datetime
    aanpasser_uri: HttpUrl
    aanpasser_omschrijving: str
    opmerkingen: Optional[str] = None
    actief: bool


class StatusCreate(StatusBase):
    @field_validator("status_id", mode="before")
    @classmethod
    def enum_validator(cls, value: str) -> str:
        Status.from_id(value)
        return value


class StatusResponse(StatusBase):
    id: int


class PlanBase(BaseModel):
    onderwerp: Optional[Annotated[str, Field(max_length=255, min_length=1)]] = None
    datum_goedkeuring: Optional[Annotated[date, Field()]] = None
    startdatum: Optional[Annotated[date, Field()]] = None
    einddatum: Optional[Annotated[date, Field()]] = None
    beheerscommissie: Optional[Annotated[bool, Field()]] = False
    geometrie: Optional[Annotated[Geometrie, Field()]] = None
    locatie_elementen: Optional[Annotated[List[LocatieElementBase], Field()]] = []
    bestanden: Optional[Annotated[List[BestandBase], Field()]] = []
    erfgoedobjecten: Optional[Annotated[List[HttpUrl], Field()]] = []
    plantype: Optional[Annotated[PlantypeBase, Field()]] = None
    relaties: Optional[Annotated[List[RelatieBase], Field()]] = []
    actief: Optional[Annotated[bool, Field()]] = None
    status: Optional[StatusBase] = None
    statussen: Optional[Annotated[List[StatusBase], Field()]] = []


class PlanCreate(PlanBase):
    """Schema for creating an Plan."""

    locatie_elementen: Optional[Annotated[List[LocatiElementCreate], Field()]] = []
    bestanden: Optional[Annotated[List[BestandCreate], Field()]] = []
    plantype: Optional[Annotated[PlantypeCreate, Field()]] = None
    relaties: Optional[Annotated[List[RelatieCreate], Field()]] = []
    actief: Optional[Annotated[bool, Field()]] = False
    status: Optional[Annotated[StatusBase, Field()]] = None
    statussen: Optional[Annotated[List[StatusCreate], Field()]] = []


class PlanUpdate(PlanBase):
    """Schema for updating an Plan."""

    pass


class PlanResponse(PlanBase):
    """Schema for Plan response."""

    id: int
    uri: str
    self: str

    model_config = ConfigDict(from_attributes=True)
