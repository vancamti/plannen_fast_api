from typing import Any
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    """Service for Plan CRUD operations."""
    
    @staticmethod
    def create_plan(db: Session, plan: PlanCreate) -> Plan:
        """Create a new plan."""
        db_plan = Plan(**plan.model_dump())
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
        """Delete an plan."""
        db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not db_plan:
            return False
        
        db.delete(db_plan)
        db.commit()
        return True
