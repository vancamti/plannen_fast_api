from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic_core import Url

from app import models, schemas
from app.mappers import plannen as mapper
from app.models import enums


@pytest.fixture
def geometrie_payload():
    return schemas.Geometrie(
        type="MultiPolygon",
        crs=schemas.CRS(
            type="name",
            properties=schemas.CRSProperties(name="EPSG:31370"),
        ),
        coordinates=[
            [
                [
                    [4.0, 51.0],
                    [4.1, 51.1],
                    [4.2, 51.2],
                    [4.0, 51.0],
                ]
            ]
        ],
    )


def test_pydantic_plan_to_db_maps_basic_fields(monkeypatch, geometrie_payload):
    fake_wkt = object()
    monkeypatch.setattr(
        mapper, "convert_geojson_to_wktelement", lambda payload: fake_wkt
    )

    relatie = schemas.RelatieCreate(
        type=schemas.RelatieTypeBase(
            id="rel-type",
            type="some-type",
            inverse="inverse-type",
        ),
        id=99,
    )
    locatie = schemas.LocatiElementCreate(
        type="https://example.com/locatie-element",
        provincie=schemas.Provincie(niscode="10", naam="Antwerpen"),
        gemeente=schemas.Gemeente(niscode="11002", naam="Antwerpen"),
    )
    plan_schema = schemas.PlanCreate(
        onderwerp="Nieuw plan",
        datum_goedkeuring=date(2022, 1, 1),
        startdatum=date(2022, 2, 1),
        einddatum=date(2022, 3, 1),
        beheerscommissie=True,
        geometrie=geometrie_payload,
        relaties=[relatie],
        locatie_elementen=[locatie],
        erfgoedobjecten=["https://example.com/erfgoed/1"],
    )

    db_plan = mapper.pydantic_plan_to_db(plan_schema)

    assert db_plan.onderwerp == "Nieuw plan"
    assert db_plan.beheerscommissie is True
    assert db_plan.geometrie is fake_wkt
    assert len(db_plan.relaties) == 1
    assert db_plan.relaties[0].relatietype_id == "rel-type"
    assert db_plan.relaties[0].naar_id == 99
    assert len(db_plan.locatie_elementen) == 1
    assert db_plan.locatie_elementen[0].provincie_naam == "Antwerpen"
    assert len(db_plan.erfgoedobjecten) == 1
    assert db_plan.erfgoedobjecten[0].erfgoedobject_id == "https://example.com/erfgoed/1"


def test_plan_db_to_pydantic_builds_response(monkeypatch):
    fake_geojson = {
        "type": "MultiPolygon",
        "crs": {"type": "name", "properties": {"name": "EPSG:31370"}},
        "coordinates": [
            [
                [
                    [
                        173351.95742557297,
                        174486.4114636053
                    ],
                    [
                        173351.22586450906,
                        174493.83912773602
                    ],
                ]
            ]

        ],
    }
    monkeypatch.setattr(
        mapper, "convert_wktelement_to_geojson", lambda value: fake_geojson
    )
    monkeypatch.setattr(
        mapper.settings, "PLANNEN_URI", "https://plannen.test/{id}"
    )

    status_enum = SimpleNamespace(id=75, naam="Actief")
    plan_status = SimpleNamespace(
        id=7,
        plan_id=1,
        status=status_enum,
        datum=datetime(2023, 1, 1, 12, 0, 0),
        aanpasser_uri="https://example.com/actor/1",
        aanpasser_omschrijving="Onroerend Erfgoed",
        opmerkingen="opmerking",
        actief=True,
    )
    plan = SimpleNamespace(
        id=1,
        onderwerp="Bestaand plan",
        datum_goedkeuring=date(2021, 5, 17),
        startdatum=date(2021, 6, 1),
        einddatum=date(2021, 12, 31),
        beheerscommissie=False,
        geometrie=object(),
        status=plan_status,
        locatie_elementen=[
            SimpleNamespace(
                id=11,
                type="https://example.com/locatie-element",
                provincie_naam="Antwerpen",
                provincie_niscode="10",
                gemeente_niscode="11002",
                gemeente_naam="Antwerpen",
            )
        ],
        bestanden=[
            SimpleNamespace(
                id=21,
                plan_id=1,
                naam="beschrijving.pdf",
                mime="application/pdf",
                bestandssoort=SimpleNamespace(id=4),
            )
        ],
        erfgoedobjecten=[
            SimpleNamespace(erfgoedobject_id="https://example.com/erfgoed/1")
        ],
        relaties=[
            SimpleNamespace(
                naar=SimpleNamespace(id=42),
                relatietype=SimpleNamespace(
                    id="rel-type",
                    type="some-type",
                    inverse="inverse-type",
                ),
            )
        ],
        statussen=[plan_status],
    )
    request = MagicMock()
    request.url_for.return_value = "https://api.test/plannen/1"

    response = mapper.plan_db_to_pydantic(plan, request)

    assert response.id == 1
    assert response.uri == "https://plannen.test/1"
    assert response.self == "https://api.test/plannen/1"
    assert response.onderwerp == "Bestaand plan"
    assert response.geometrie.type == "MultiPolygon"
    assert response.locatie_elementen[0].provincie.naam == "Antwerpen"
    assert response.bestanden[0].bestandssoort_id == 4
    assert response.erfgoedobjecten == [Url("https://example.com/erfgoed/1")]
    assert response.relaties[0].id == 42
    assert response.relaties[0].type.id == "rel-type"
    assert response.statussen[0].status_id == 75
    assert response.status.status_id == 75
    assert response.actief is True


def test_pydantic_bestand_to_db_reuses_existing_instance():
    bestaande_bestand = models.PlanBestand(
        id=5,
        plan_id=2,
        naam="oud.pdf",
        mime="application/pdf",
        bestandssoort=enums.Bestandssoort.PLAN,
    )
    bestand_schema = schemas.BestandUpdate(
        naam="nieuw.pdf",
        bestandssoort_id=1,
        temporary_storage_key="temp-key",
        mime="application/pdf",
    )

    resultaat = mapper.pydantic_bestand_to_db(
        bestand_schema,
        plan_id=10,
        existing=bestaande_bestand,
    )

    assert resultaat is bestaande_bestand
    assert bestaande_bestand.plan_id == 10
    assert bestaande_bestand.naam == "nieuw.pdf"
    assert bestaande_bestand.mime == "application/pdf"
    assert bestaande_bestand.bestandssoort == enums.Bestandssoort.BEHEERSPLAN
    assert bestaande_bestand.temporary_storage_key == "temp-key"
