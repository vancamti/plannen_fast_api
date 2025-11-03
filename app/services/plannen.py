from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.mappers.plannen import pydantic_bestand_to_db
from app.mappers.plannen import pydantic_plan_to_db
from app.mappers.plannen import pydantic_status_to_db
from app.models import Plan
from app.models import PlanBestand
from app.models import PlanStatus
from app.schemas import BestandCreate
from app.schemas import BestandUpdate
from app.schemas import StatusCreate
from app.schemas.plannen import PlanCreate
from app.schemas.plannen import PlanUpdate


class PlanService:
    """Service for Plan CRUD operations."""

    @staticmethod
    def create_plan(request: Request, db: Session, plan: PlanCreate) -> Plan:
        """Create a new plan."""
        db_plan = pydantic_plan_to_db(plan)
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)

        return db_plan

    @staticmethod
    def get_plan(db: Session, plan_id: int) -> Optional[Plan]:
        """Get plan by ID."""
        return db.query(Plan).filter(Plan.id == plan_id).first()

    @staticmethod
    def get_plannen(db: Session, skip: int = 0, limit: int = 100) -> list[type[Plan]]:
        """Get list of plans with pagination."""
        return db.query(Plan).offset(skip).limit(limit).all()

    @staticmethod
    def update_plan(db: Session, existing: Plan, plan: PlanUpdate) -> Optional[Plan]:
        """Update an existing plan."""
        db_plan = pydantic_plan_to_db(plan, existing=existing)
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)

        return db_plan

    @staticmethod
    def delete_plan(db: Session, plan_id: int) -> bool:
        """Delete a plan."""
        db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not db_plan:
            return False

        db.delete(db_plan)
        db.commit()
        return True

    @staticmethod
    def add_bestand(
        db: Session, plan_id: int, bestand: BestandCreate
    ) -> PlanBestand | None:
        """Add a bestand to a plan."""
        bestand = pydantic_bestand_to_db(bestand, plan_id)
        db.add(bestand)
        db.commit()
        db.refresh(bestand)
        return bestand

    @staticmethod
    def update_bestand(
        db: Session, existing: PlanBestand, bestand_data: BestandUpdate
    ) -> Optional[PlanBestand]:
        """Update a bestand of a plan."""
        db_bestand = pydantic_bestand_to_db(
            bestand_data, existing.plan_id, existing=existing
        )
        db.add(db_bestand)
        db.commit()
        db.refresh(db_bestand)
        return db_bestand

    @staticmethod
    def delete_bestand(db: Session, db_bestand: PlanBestand) -> bool:
        """Delete a bestand from a plan."""
        db.delete(db_bestand)
        db.commit()
        return True

    @staticmethod
    def add_status(
        db: Session, plan_id: int, status: StatusCreate
    ) -> PlanStatus | None:
        """Add a status to a plan."""
        status = pydantic_status_to_db(status, plan_id)
        db.add(status)
        db.commit()
        db.refresh(status)
        return status

    def get_statussen(db: Session, plan_id: int) -> list[type[PlanStatus]]:
        """Get all statuses for a plan."""
        return db.query(PlanStatus).filter(PlanStatus.plan_id == plan_id).all()

    @staticmethod
    def delete_status(db: Session, db_status: PlanStatus) -> bool:
        """Delete a status from a plan."""
        db.delete(db_status)
        db.commit()
        return True
