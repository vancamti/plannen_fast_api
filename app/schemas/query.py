from oe_utils.validation.pydantic_es_filters import IntQueryparam
from oe_utils.validation.pydantic_es_filters import StrQueryparam
from pydantic import BaseModel
from pydantic import Field
from datetime import date

class BaseFilterParams(BaseModel):
    sort: str | None = None
    tekst: str | None = None


class FilterParams(BaseFilterParams):
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

    sort: StrQueryparam | None = Field(
        None,
        description="Veld om op te sorteren. Gebruik - en + om de "
                    "volgorde aan te duiden. Bv. naam of +naam sorteert "
                    "oplopend op naam, -naam sorteer aflopend op naam.",
    )
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

def get_filter_query(
    sort: str | None = None,
    tekst: str | None = None,
    id: IntQueryparam | None = None,
    onderwerp: StrQueryparam | None = None,
    gemeente: StrQueryparam | None = None,
    provincie: StrQueryparam | None = None,
    erfgoedobjecten: StrQueryparam | None = None,
    aanduidingsobject: StrQueryparam | None = None,
    plantype: StrQueryparam | None = None,
    type: StrQueryparam | None = None,
    status: StrQueryparam | None = None,
    beheerscommissie: StrQueryparam | None = None,
    jaar_goedkeuring: StrQueryparam | None = None,
    datum_goedkeuring_van: date | None = None,
    datum_goedkeuring_tot: date | None = None,
    beheersplan_verlopen: bool | None = None,
    aanduidingsobjecttype: StrQueryparam | None = None,
) -> FilterParams:
    return FilterParams(
        sort=sort,
        tekst=tekst,
        id=id,
        onderwerp=onderwerp,
        gemeente=gemeente,
        provincie=provincie,
        erfgoedobjecten=erfgoedobjecten,
        aanduidingsobject=aanduidingsobject,
        plantype=plantype,
        type=type,
        status=status,
        beheerscommissie=beheerscommissie,
        jaar_goedkeuring=jaar_goedkeuring,
        datum_goedkeuring_van=datum_goedkeuring_van,
        datum_goedkeuring_tot=datum_goedkeuring_tot,
        beheersplan_verlopen=beheersplan_verlopen,
        aanduidingsobjecttype=aanduidingsobjecttype,
    )