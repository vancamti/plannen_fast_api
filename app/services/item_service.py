from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    """Service for Item CRUD operations."""
    
    @staticmethod
    def create_item(db: Session, item: ItemCreate) -> Item:
        """Create a new item."""
        db_item = Item(**item.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def get_item(db: Session, item_id: int) -> Optional[Item]:
        """Get item by ID."""
        return db.query(Item).filter(Item.id == item_id).first()
    
    @staticmethod
    def get_items(db: Session, skip: int = 0, limit: int = 100) -> List[Item]:
        """Get list of items with pagination."""
        return db.query(Item).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_item(db: Session, item_id: int, item: ItemUpdate) -> Optional[Item]:
        """Update an existing item."""
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return None
        
        update_data = item.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def delete_item(db: Session, item_id: int) -> bool:
        """Delete an item."""
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return False
        
        db.delete(db_item)
        db.commit()
        return True
