from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.services.plan_service import PlanService

router = APIRouter()


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan: PlanCreate,
    db: Session = Depends(get_db)
):
    """Create a new plan."""
    return PlanService.create_plan(db=db, plan=plan)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Get plan by ID."""
    db_plan = PlanService.get_plan(db=db, plan_id=plan_id)
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    return db_plan


@router.get("/", response_model=List[PlanResponse])
def get_plannen(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of plannen."""
    return PlanService.get_plannen(db=db, skip=skip, limit=limit)


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    plan: PlanUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing plan."""
    db_plan = PlanService.update_plan(db=db, plan_id=plan_id, plan=plan)
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    return db_plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Delete a plan."""
    success = PlanService.delete_plan(db=db, plan_id=plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
