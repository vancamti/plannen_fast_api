# Session-level event listeners
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models import PlanBestand


@event.listens_for(Session, "after_flush", propagate=True)
def receive_after_flush(session, flush_context):
    """Handle after_flush events for new and dirty objects."""
    content_manager = session.info.get('content_manager')
    if content_manager is None:
        return  # No content manager attached (e.g., in tests)

    # Handle new objects
    for obj in session.new:
        if isinstance(obj, PlanBestand) and obj.temporary_storage_key is not None:
            content_manager.copy_temp_content(
                obj.temporary_storage_key,
                obj.plan_id,
                obj.id
            )

    # Handle dirty (updated) objects
    for obj in session.dirty:
        if isinstance(obj, PlanBestand) and obj.temporary_storage_key is not None:
            content_manager.copy_temp_content(
                obj.temporary_storage_key,
                obj.plan_id,
                obj.id
            )


@event.listens_for(Session, "after_flush", propagate=True)
def receive_after_flush_delete(session, flush_context):
    """Handle deletions."""
    content_manager = session.info.get('content_manager')
    if content_manager is None:
        return

    for obj in session.deleted:
        if isinstance(obj, PlanBestand):
            content_manager.remove_content(obj.plan_id, obj.id)