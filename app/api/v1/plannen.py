from typing import Annotated
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi import File
from fastapi import Form
from fastapi import UploadFile
from sqlalchemy.orm import Session
from storageprovider.client import StorageProviderClient

from app.core.dependencies import get_content_manager
from app.core.dependencies import get_storage_provider
from app.db.base import get_db
from app.mappers.plannen import bestand_db_to_pydantic
from app.mappers.plannen import plan_db_to_pydantic
from app.schemas import BestandCreate
from app.schemas import BestandResponse
from app.schemas.plannen import PlanCreate, PlanUpdate, PlanResponse
from app.services.plannen import PlanService
from app.storage.conent_manager import ContentManager

router = APIRouter()


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(request: Request, plan: PlanCreate, db: Session = Depends(get_db)):
    """Create a new plan."""
    db_plan = PlanService.create_plan(request=request, db=db, plan=plan)
    return plan_db_to_pydantic(db_plan, request)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(request: Request, plan_id: int, db: Session = Depends(get_db)):
    """Get plan by ID."""
    db_plan = PlanService.get_plan(db=db, plan_id=plan_id)
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )
    return plan_db_to_pydantic(db_plan, request)


@router.get("/", response_model=List[PlanResponse])
def get_plannen(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of plannen."""
    return PlanService.get_plannen(db=db, skip=skip, limit=limit)


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, plan: PlanUpdate, db: Session = Depends(get_db)):
    """Update an existing plan."""
    db_plan = PlanService.update_plan(db=db, plan_id=plan_id, plan=plan)
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )
    return db_plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a plan."""
    success = PlanService.delete_plan(db=db, plan_id=plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

@router.post("/temp/bestanden")
def upload_to_temp(
    file: UploadFile,
    content_manager: ContentManager = Depends(get_content_manager),
):
    """Upload a file to temporary storage"""
    file.file.seek(0)
    temp_key = content_manager.store_file_content_to_temp_location(file.file)
    return {"temporary_storage_key": temp_key}


@router.post("/{plan_id}/bestanden", response_model=BestandResponse)
def add_bestand(
        plan_id: int,
        request: dict,  # Accept raw dict first
        db: Session = Depends(get_db),
        content_manager: ContentManager = Depends(get_content_manager),
        storageprovider: StorageProviderClient = Depends(get_storage_provider),
):
    # Validate with context
    bestand_pydantic = BestandCreate.model_validate(
        request,
        context={
            "content_manager": content_manager,
            "storageprovider": storageprovider,
        }
    )
    bestand = PlanService.add_bestand(db,plan_id, bestand_pydantic)

    return bestand_db_to_pydantic(bestand)