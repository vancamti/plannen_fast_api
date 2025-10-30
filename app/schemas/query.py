from datetime import date

from oe_utils.validation.pydantic_es_filters import IntQueryparam
from oe_utils.validation.pydantic_es_filters import StrQueryparam
from pydantic import BaseModel
from pydantic import Field


class FilterParams(BaseModel):
    sort: str | None = None
    tekst: str | None = None
    id: IntQueryparam | None = None
    onderwerp: StrQueryparam | None = None
    gemeente: StrQueryparam | None = None
    provincie: StrQueryparam | None = None
    erfgoedobjecten: StrQueryparam | None = None
    aanduidingsobject: StrQueryparam | None = None
    plantype: StrQueryparam | None = None
    type: StrQueryparam | None = None
    status: StrQueryparam | None = None
    beheerscommissie: StrQueryparam | None = None
    jaar_goedkeuring: StrQueryparam | None = None
    datum_goedkeuring_van: date | None = None
    datum_goedkeuring_tot: date | None = None
    beheersplan_verlopen: bool | None = None
    aanduidingsobjecttype: StrQueryparam | None = None

    per_pagina: int | None = Field(
        None,
        ge=1,
        description="Maximum aantal resultaten per pagina",
    )
    pagina: int | None = Field(
        None,
        ge=1,
        description="Op te halen pagina indien er vele resultaten zijn.",
    )
