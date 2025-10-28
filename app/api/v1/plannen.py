import re
from io import BytesIO
from typing import Annotated
from typing import List
from zipfile import ZipFile

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import UploadFile
from fastapi import status
from minio.error import MinioException
from oeauth.openid import OpenIDHelper
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.responses import StreamingResponse
from storageprovider.client import StorageProviderClient

from app.core.dependencies import get_bestand_or_404
from app.core.dependencies import get_content_manager
from app.core.dependencies import get_db
from app.core.dependencies import get_plan_or_404
from app.core.dependencies import get_status_or_404
from app.core.dependencies import get_storage_provider
from app.core.dependencies import get_token_provider
from app.mappers.plannen import bestand_db_to_pydantic
from app.mappers.plannen import plan_db_to_pydantic
from app.mappers.plannen import status_db_to_pydantic
from app.models import Plan
from app.models import PlanBestand
from app.models import PlanStatus
from app.schemas import BestandCreate
from app.schemas import BestandResponse
from app.schemas import BestandUpdate
from app.schemas import StatusResponse
from app.schemas.errors import NotFoundResponse
from app.schemas.plannen import PlanCreate
from app.schemas.plannen import PlanResponse
from app.schemas.plannen import PlanUpdate
from app.schemas.query import FilterParams
from app.schemas.query import get_filter_query
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
def get_plannen(filter_query: FilterParams = Depends(get_filter_query)):
    """Get list of plannen."""
    return PlanService.get_plannen()


@router.put(
    "/{object_id}",
    response_model=PlanResponse,
    responses={
        "200": {"model": PlanResponse, "description": "The updated plan"},
        "404": {"model": NotFoundResponse, "description": "Plan not found"},
    }
)
def update_plan(
        request: Request,
        plan: PlanUpdate,
        existing: Plan = Depends(get_plan_or_404),
        db: Session = Depends(get_db)
):
    """Update an existing plan."""
    db_plan = PlanService.update_plan(db=db, existing=existing, plan=plan)
    return plan_db_to_pydantic(db_plan, request)


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
    bestand = PlanService.add_bestand(db, plan_id, bestand_pydantic)
    return bestand_db_to_pydantic(bestand)


@router.get(
    "/{plan_id}/bestanden/{object_id}",
    responses={
        200: {
            "description": "Bestand content in either JSON or binary depending on Accept header.",
            "content": {
                "application/octet-stream": {
                    # For binary responses, OpenAPI uses type=string, format=binary
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
        "404": {"model": NotFoundResponse, "description": "Plan or Bestand not found"},
    },
)
def get_bestand(
        plan_id: int,
        bestand: PlanBestand = Depends(get_bestand_or_404),
        content_manager: ContentManager = Depends(get_content_manager),
        _token_provider: OpenIDHelper = Depends(get_token_provider),
):
    try:
        iter_content = content_manager.get_object_streaming(plan_id, bestand.id)
        bestandsnaam = re.sub('[\\\\/:*?"<>| ]', '_', bestand.naam)
        content_disposition = f'attachment; filename="{bestandsnaam.encode("utf-8").decode("latin-1")}"'
        return StreamingResponse(
            content=iter(iter_content),
            media_type=bestand.mime,
            headers={
                "Content-Disposition": content_disposition
            }
        )
    except MinioException as me:
        raise HTTPException(detail=repr(me), status_code=status.HTTP_404_NOT_FOUND)


@router.get(
    "/{object_id}/bestanden",
    response_model=List[BestandResponse],
    responses={
        200: {
            "description": "Bestanden in either JSON or ZIP depending on Accept header.",
            "content": {
                "application/zip": {
                    # For binary responses, OpenAPI uses type=string, format=binary
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
        "404": {"model": NotFoundResponse, "description": "Plan not found"},
    },
)
def get_bestanden(
        request: Request, object_id: int,
        plan: Plan = Depends(get_plan_or_404),
        storage_provider: StorageProviderClient = Depends(get_storage_provider),
        _token_provider: OpenIDHelper = Depends(get_token_provider),
):
    """Get list of bestanden for a plan."""
    accept = request.headers.get("accept", "application/json")
    if "application/json" in accept:
        return [bestand_db_to_pydantic(bestand) for bestand in plan.bestanden]
    elif "application/zip" in accept:
        translations = {
            str(bestand.id).zfill(3): bestand.naam
            for bestand in plan.bestanden
        }
        if not translations:
            # create an empty zip file
            zip_data = BytesIO()
            with ZipFile(zip_data, "w"):
                pass
            zip_data.seek(0)
            zip_data = zip_data.read()
        else:
            zip_data = storage_provider.get_container_data(
                str(object_id),
                system_token=_token_provider.get_system_token(),
                translations=translations
            )
        return Response(
            content=zip_data,
            media_type='application/zip',
            headers={
                "Content-Disposition": f"attachment; filename=plan_{object_id}_bestanden.zip",
                "content-type": "application/zip",
                "content-length": str(len(zip_data)),
            }
        )


@router.put(
    "/{plan_id}/bestanden/{object_id}",
    response_model=BestandResponse,
    responses={
        "200": {"model": PlanResponse, "description": "The updated plan"},
        "404": {"model": NotFoundResponse, "description": "Plan not found"},
    }
)
def update_bestand(
        request: Request,
        bestand: BestandUpdate,
        existing: PlanBestand = Depends(get_bestand_or_404),
        db: Session = Depends(get_db)
):
    """Update an existing plan."""
    db_plan = PlanService.update_bestand(db=db, existing=existing, bestand_data=bestand)
    return bestand_db_to_pydantic(db_plan, request)


@router.delete("/{plan_id}/bestanden/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_betand(existing: PlanBestand = Depends(get_bestand_or_404), db: Session = Depends(get_db)):
    PlanService.delete_bestand(db=db, db_bestand=existing)


@router.post(
    "/plan/{object_id}/statussen",
    response_model=StatusResponse,
    status_code=status.HTTP_201_CREATED
)
def create_status(request: Request, plan: PlanCreate, db: Session = Depends(get_db)):
    """Create a new plan."""
    db_plan = PlanService.create_plan(request=request, db=db, plan=plan)
    return plan_db_to_pydantic(db_plan, request)

    return bestand_db_to_pydantic(bestand)


@router.get(
    "/{object_id}/statussen",
    response_model=List[StatusResponse],
    responses={
        200: {"model": List[StatusResponse], "description": "List of statussen for the plan"},
        404: {"model": NotFoundResponse, "description": "Plan not found"},
    },
)
def get_statussen(
        plan: Plan = Depends(get_plan_or_404),
):
    """Get list of bestanden for a plan."""
    return [status_db_to_pydantic(status) for status in plan.statussen]


@router.get(
    "/{plan_id}/statussen/{object_id}",
    response_model=StatusResponse,
    responses={
        200: {"model": StatusResponse, "description": "List of statussen for the plan"},
        404: {"model": NotFoundResponse, "description": "Status not found"},
    },
)
def get_status(
        status: PlanStatus = Depends(get_status_or_404),
):
    """ """
    return status_db_to_pydantic(status)
