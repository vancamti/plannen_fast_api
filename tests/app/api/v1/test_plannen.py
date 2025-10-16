from datetime import date

from httpx import Client
from sqlalchemy.orm import Session

from app.models.plan import Plan


def plan_payload(**overrides) -> dict:
    payload = {
        "onderwerp": "Test Plan",
        "datum_goedkeuring": date(2023, 1, 1).isoformat(),
        "startdatum": date(2023, 1, 1).isoformat(),
        "einddatum": date(2023, 12, 31).isoformat(),
        "beheerscommissie": True,
    }
    payload.update(overrides)
    return payload


def test_create_plan_returns_created_plan(
    test_client: Client,
    db_session: Session,
) -> None:
    response = test_client.post("/api/v1/plannen/", json=plan_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["onderwerp"] == "Test Plan"

    db_count = db_session.query(Plan).count()
    assert db_count == 1


def test_get_plan_returns_plan(test_client: Client) -> None:
    created = test_client.post("/api/v1/plannen/", json=plan_payload()).json()

    response = test_client.get(f"/api/v1/plannen/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_plan_not_found_returns_404(test_client: Client) -> None:
    response = test_client.get("/api/v1/plannen/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan not found"


def test_get_plannen_returns_list(test_client: Client) -> None:
    test_client.post(
        "/api/v1/plannen/",
        json=plan_payload(onderwerp="Plan A"),
    )
    test_client.post(
        "/api/v1/plannen/",
        json=plan_payload(onderwerp="Plan B"),
    )

    response = test_client.get("/api/v1/plannen/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    onderwerpen = {item["onderwerp"] for item in data}
    assert onderwerpen == {"Plan A", "Plan B"}


def test_update_plan_updates_fields(test_client: Client) -> None:
    created = test_client.post("/api/v1/plannen/", json=plan_payload()).json()

    response = test_client.put(
        f"/api/v1/plannen/{created['id']}",
        json=plan_payload(onderwerp="Updated Plan", beheerscommissie=False),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["onderwerp"] == "Updated Plan"
    assert data["beheerscommissie"] is False


def test_update_plan_not_found_returns_404(
    test_client: Client,
) -> None:
    response = test_client.put(
        "/api/v1/plannen/999",
        json=plan_payload(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan not found"


def test_delete_plan_removes_plan(test_client: Client) -> None:
    created = test_client.post("/api/v1/plannen/", json=plan_payload()).json()

    response = test_client.delete(f"/api/v1/plannen/{created['id']}")

    assert response.status_code == 204

    follow_up = test_client.get(f"/api/v1/plannen/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_plan_not_found_returns_404(
    test_client: Client,
) -> None:
    response = test_client.delete("/api/v1/plannen/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan not found"
