from datetime import date

import pytest
from httpx import Client
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models.plan import Plan

def plan_payload(**overrides) -> dict:
    payload = {
    "id": 0,
    "onderwerp": "Test Plan",
    "beheerscommissie": True,
    "plantype": {
        "uri": "https://dev-id.erfgoed.net/thesauri/plantypes/GEIB",
        "label": {}
    },
    "plantype_naam": "test",
    "datum_goedkeuring": "2025-10-01",
    "startdatum": "2025-10-01",
    "einddatum": "2049-10-01",
    "bestanden": [],
    "locatie_elementen": [
        {
            "type": "https://id.erfgoed.net/vocab/ontology#LocatieElement",
            "provincie": {
                "niscode": "20001",
                "naam": "Vlaams-Brabant"
            },
            "gemeente": {
                "niscode": "24062",
                "naam": "Leuven"
            }
        }
    ],
    "erfgoedobjecten": [
        "https://dev-id.erfgoed.net/aanduidingsobjecten/61"
    ],
    "geometrie": {
        "type": "MultiPolygon",
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
                    [
                        173349.0592947988,
                        174500.98135089967
                    ],
                    [
                        173345.54097650107,
                        174507.5636614655
                    ],
                    [
                        173340.806116615,
                        174513.33310492986
                    ],
                    [
                        173335.03667315064,
                        174518.06796481594
                    ],
                    [
                        173328.4543625848,
                        174521.58628311366
                    ],
                    [
                        173321.31213942115,
                        174523.75285282393
                    ],
                    [
                        173313.88447529043,
                        174524.48441388784
                    ],
                    [
                        173306.4568111597,
                        174523.75285282393
                    ],
                    [
                        173299.31458799605,
                        174521.58628311366
                    ],
                    [
                        173292.73227743022,
                        174518.06796481594
                    ],
                    [
                        173286.96283396587,
                        174513.33310492986
                    ],
                    [
                        173282.22797407978,
                        174507.5636614655
                    ],
                    [
                        173278.70965578206,
                        174500.98135089967
                    ],
                    [
                        173276.5430860718,
                        174493.83912773602
                    ],
                    [
                        173275.81152500788,
                        174486.4114636053
                    ],
                    [
                        173276.5430860718,
                        174478.98379947458
                    ],
                    [
                        173278.70965578206,
                        174471.84157631092
                    ],
                    [
                        173282.22797407978,
                        174465.2592657451
                    ],
                    [
                        173286.96283396587,
                        174459.48982228074
                    ],
                    [
                        173292.73227743022,
                        174454.75496239465
                    ],
                    [
                        173299.31458799605,
                        174451.23664409693
                    ],
                    [
                        173306.4568111597,
                        174449.07007438666
                    ],
                    [
                        173313.88447529043,
                        174448.33851332276
                    ],
                    [
                        173321.31213942115,
                        174449.07007438666
                    ],
                    [
                        173328.4543625848,
                        174451.23664409693
                    ],
                    [
                        173335.03667315064,
                        174454.75496239465
                    ],
                    [
                        173340.806116615,
                        174459.48982228074
                    ],
                    [
                        173345.54097650107,
                        174465.2592657451
                    ],
                    [
                        173349.0592947988,
                        174471.84157631092
                    ],
                    [
                        173351.22586450906,
                        174478.98379947458
                    ],
                    [
                        173351.95742557297,
                        174486.4114636053
                    ]
                ]
            ]
        ],
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::31370"
            }
        }
    },
    "statussen": [
        {
            "status_id": 10,
            "naam": "Klad",
            "datum": "2025-10-16T16:11:32.598222+02:00",
            "aanpasser_uri": "https://dev-id.erfgoed.net/actoren/12761",
            "aanpasser_omschrijving": "Van Campenhout, Tim",
            "opmerkingen": None,
            "actief": False
        }
    ],
    "relaties": []
}
    payload.update(overrides)
    return payload


def test_create_plan_returns_created_plan(
    test_app: TestClient,
    db_session: Session,
) -> None:
    response = test_app.post("/api/v1/plannen/", json=plan_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["onderwerp"] == "Test Plan"

    db_count = db_session.query(Plan).count()
    assert db_count == 1


def test_get_plan_returns_plan(test_app: TestClient) -> None:
    created = test_app.post("/api/v1/plannen/", json=plan_payload()).json()
    response = test_app.get(f"/api/v1/plannen/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_plan_not_found_returns_404(test_app: Client) -> None:
    response = test_app.get("/api/v1/plannen/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan not found"


def test_update_plan_updates_fields(test_app: Client) -> None:
    created = test_app.post("/api/v1/plannen/", json=plan_payload()).json()

    response = test_app.put(
        f"/api/v1/plannen/{created['id']}",
        json=plan_payload(onderwerp="Updated Plan", beheerscommissie=False),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["onderwerp"] == "Updated Plan"
    assert data["beheerscommissie"] is False


def test_update_plan_not_found_returns_404(
    test_app: Client,
) -> None:
    response = test_app.put(
        "/api/v1/plannen/999",
        json=plan_payload(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan with id 999 not found"


def test_delete_plan_removes_plan(test_app: Client) -> None:
    created = test_app.post("/api/v1/plannen/", json=plan_payload()).json()
    response = test_app.delete(f"/api/v1/plannen/{created['id']}")

    assert response.status_code == 204

    follow_up = test_app.get(f"/api/v1/plannen/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_plan_not_found_returns_404(
    test_app: Client,
) -> None:
    response = test_app.delete("/api/v1/plannen/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan not found"
