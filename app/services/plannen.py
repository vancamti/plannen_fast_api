from typing import Any
from typing import Any
from typing import List, Optional
from fastapi import Request
from oe_geoutils.utils import convert_geojson_to_wktelement
from sqlalchemy.orm import Session

from app.mappers.plannen import pydantic_bestand_to_db
from app.mappers.plannen import pydantic_plan_to_db
from app.models import Plan
from app.models import PlanBestand
from app.schemas import BestandCreate
from app.schemas.plannen import PlanCreate, PlanUpdate


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
    def update_plan(db: Session, plan_id: int, plan: PlanUpdate) -> Optional[Plan]:
        """Update an existing plan."""
        db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not db_plan:
            return None

        update_data = plan.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_plan, field, value)

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
    def add_bestand(db: Session, plan_id: int, bestand: BestandCreate) -> PlanBestand | None:
        """Add a bestand to a plan."""
        bestand = pydantic_bestand_to_db(bestand,plan_id)
        db.add(bestand)
        db.commit()
        db.refresh(bestand)
        return bestand