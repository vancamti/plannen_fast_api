from typing import List

from geoalchemy2 import WKTElement
from oe_geoutils.utils import convert_geojson_to_wktelement
from oe_geoutils.utils import convert_wktelement_to_geojson
from starlette.requests import Request

from app import models
from app import schemas
from app.constants import SETTINGS
from app.models import enums


def pydantic_plan_to_db(plan: schemas.PlanCreate) -> models.Plan:
    """map a pydantic PlanCreate to a SQLAlchemy Plan model."""
    return models.Plan(
        onderwerp=plan.onderwerp,
        datum_goedkeuring=plan.datum_goedkeuring,
        startdatum=plan.startdatum,
        einddatum=plan.einddatum,
        beheerscommissie=plan.beheerscommissie,
        geometrie=pydantic_geometrie_to_db(plan.geometrie),
        relaties=pydantic_relaties_to_db(plan.relaties),
        statussen=pydantic_statussen_to_db(plan.statussen),
        locatie_elementen=pydantic_locatie_elementen_to_db(plan.locatie_elementen),
        bestanden=pydantic_bestanden_to_db(plan.bestanden),
        erfgoedobjecten=pydantic_erfgoedobjecten_to_db(plan.erfgoedobjecten),
    )


def pydantic_geometrie_to_db(geometrie: schemas.Geometrie) -> WKTElement:
    """Map a pydantic Geometrie to a WKTElement."""
    return convert_geojson_to_wktelement(geometrie.model_dump())


def pydantic_relaties_to_db(
    relaties: List[schemas.RelatieCreate],
) -> List[models.PlanRelatie]:
    """Map a list of pydantic RelatieCreate to a list of SQLAlchemy PlanRelatie models."""
    return [
        models.PlanRelatie(
            relatietype_id=relatie.type.id,
            naar_id=relatie.id,
        )
        for relatie in relaties
    ]


def pydantic_erfgoedobjecten_to_db(
    erfgoedobjecten: List[str],
) -> List[models.PlanErfgoedobject]:
    """Map a list of pydantic erfgoedobject IDs to a list of SQLAlchemy PlanErfgoedobject models."""
    return [
        models.PlanErfgoedobject(erfgoedobject_id=str(erfgoedobject))
        for erfgoedobject in erfgoedobjecten
    ]


def pydantic_statussen_to_db(
    statussen: List[schemas.StatusCreate],
) -> List[models.PlanStatus]:
    """Map a list of pydantic StatusCreate to a list of SQLAlchemy PlanStatus models."""
    return [
        models.PlanStatus(
            status=enums.Status.from_id(status.status_id),
            datum=status.datum,
            aanpasser_uri=str(status.aanpasser_uri),
            aanpasser_omschrijving=status.aanpasser_omschrijving,
            opmerkingen=status.opmerkingen,
        )
        for status in statussen
    ]


def pydantic_locatie_elementen_to_db(
    locatie_elementen: List[schemas.LocatiElementCreate],
) -> List[models.LocatieElement]:
    """Map a list of pydantic LocatieElementCreate to a list of SQLAlchemy LocatieElement models."""
    return [
        models.LocatieElement(
            type=str(element.type),
            provincie_naam=element.provincie.naam,
            provincie_niscode=element.provincie.niscode,
            gemeente_niscode=element.gemeente.niscode,
            gemeente_naam=element.gemeente.naam,
        )
        for element in locatie_elementen
    ]


def pydantic_bestanden_to_db(
    bestanden: List[schemas.BestandCreate],
) -> List[models.PlanBestand]:
    """Map a list of pydantic BestandCreate to a list of SQLAlchemy Bestand models."""
    return [
        models.PlanBestand(
            bestandssoort=enums.Bestandssoort.from_id(bestand.bestandssoort_id),
            mime=bestand.mime,
            naam=bestand.naam,
        )
        for bestand in bestanden
    ]


def plan_db_to_pydantic(plan: models.Plan, request: Request= None) -> schemas.PlanResponse:
    """Map a SQLAlchemy Plan model to a pydantic PlanResponse."""
    return schemas.PlanResponse(
        id=plan.id,
        uri=SETTINGS["PLANNEN_URI"].format(id=plan.id),
        self=str(request.url_for("get_plan", plan_id=plan.id)),
        onderwerp=plan.onderwerp,
        datum_goedkeuring=plan.datum_goedkeuring,
        startdatum=plan.startdatum,
        einddatum=plan.einddatum,
        beheerscommissie=plan.beheerscommissie,
        actief=plan.status.actief if plan.status else False,
        geometrie=schemas.Geometrie(**convert_wktelement_to_geojson(plan.geometrie)),
        locatie_elementen=[
            locatie_element_db_to_pydantic(element)
            for element in plan.locatie_elementen
        ],
        bestanden=[bestand_db_to_pydantic(bestand) for bestand in plan.bestanden],
        erfgoedobjecten=[
            erfgoedobject.erfgoedobject_id for erfgoedobject in plan.erfgoedobjecten
        ],
        relaties=[relatie_db_to_pydantic(relatie) for relatie in plan.relaties],
        statussen=[status_db_to_pydantic(status) for status in plan.statussen],
        status=status_db_to_pydantic(plan.status) if plan.status else None,
    )


def locatie_element_db_to_pydantic(
    element: models.LocatieElement,
) -> schemas.LocatieElementResponse:
    """Map a SQLAlchemy LocatieElement model to a pydantic LocatieElementResponse."""
    return schemas.LocatieElementResponse(
        id=element.id,
        type=element.type,
        provincie=schemas.Provincie(
            niscode=element.provincie_niscode,
            naam=element.provincie_naam,
        ),
        gemeente=schemas.Gemeente(
            niscode=element.gemeente_niscode,
            naam=element.gemeente_naam,
        ),
    )


def bestand_db_to_pydantic(
    bestand: models.PlanBestand, request: Request = None
) -> schemas.BestandResponse:
    """Map a SQLAlchemy PlanBestand model to a pydantic BestandResponse."""
    return schemas.BestandResponse(
        id=bestand.id,
        plan_id=bestand.plan_id,
        naam=bestand.naam,
        mime=bestand.mime,
        bestandssoort_id=bestand.bestandssoort.value,
    )


def status_db_to_pydantic(
    status: models.PlanStatus, request: Request = None
) -> schemas.StatusResponse:
    """Map a SQLAlchemy PlanStatus model to a pydantic StatusResponse."""
    return schemas.StatusResponse(
        id=status.id,
        status_id=status.status.id,
        naam=status.status.naam,
        datum=status.datum,
        aanpasser_uri=status.aanpasser_uri,
        aanpasser_omschrijving=status.aanpasser_omschrijving,
        opmerkingen=status.opmerkingen,
        actief=status.actief,
    )


def relatie_db_to_pydantic(
    relatie: models.PlanRelatie, request: Request = None
) -> schemas.RelatieResponse:
    """Map a SQLAlchemy PlanRelatie model to a pydantic RelatieResponse."""
    return schemas.RelatieResponse(
        id=relatie.naar.id,
        type=schemas.RelatieTypeResponse(
            id=relatie.relatietype.id,
            type=relatie.relatietype.type,
            inverse=relatie.relatietype.inverse,
        ),
    )
