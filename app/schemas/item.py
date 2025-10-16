from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    """Base schema for Item."""
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    """Schema for creating an Item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an Item."""
    title: Optional[str] = None
    description: Optional[str] = None


class ItemResponse(ItemBase):
    """Schema for Item response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
