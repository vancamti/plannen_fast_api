import itertools as it
import logging
import uuid

from oe_utils.jobs import queue_job
from oe_utils.search.searchengine import SearchEngine
from oe_utils.utils.db_utils import db_session
from requests import HTTPError
from sqlalchemy import event
from sqlalchemy import select
from sqlalchemy.orm import object_session

log = logging.getLogger()


class IndexingWorker:
    def __init__(self, db_class, search_engine: SearchEngine, settings):
        super().__init__()
        self.search_engine = search_engine
        self.settings = settings
        self.db_class = db_class

    def index_operation(self, index_new, index_dirty, index_deleted):
        """
        Execute an index operation.

        This operation can contain mutiple adds, deletes and updates.
        :param list index_new: New model id's to index.
        :param list index_dirty: model that have changed and need an update in the index
        :param list index_deleted: model that need to be deleted from the index
        """
        log.info("starting index operation")
        with db_session() as session:
            for object_id in it.chain(index_new, index_dirty):
                self.index(session, object_id)
            for object_id in index_deleted:
                self.delete(object_id)

    def index(self, session, object_id):
        db_object = self.get_database_object(session, object_id)
        if db_object is not None:
            self.add_to_index(db_object, session)
            return True
        else:
            log.warning(
                "Geprobeerd een %s te indexeren die niet aanwezig was: %d",
                self.db_class.__name__,
                object_id,
            )
            return False

    def get_database_object(self, session, object_id):
        return session.scalars(
            select(self.db_class).filter(self.db_class.id == object_id)
        ).first()

    def add_to_index(self, db_object, session):
        self.search_engine.add_to_index(
            object_id=db_object.id,
            object_data=self.serialize_object(db_object, session),
        )

    def delete(self, object_id):
        try:
            self.search_engine.remove_from_index_by_query("id", object_id)
            return True
        except HTTPError:
            log.warning(
                "Geprobeerd een %s te vewijderen uit de ES index die niet "
                "aanwezig was: %d",
                self.db_class.__name__,
                object_id,
            )
            return False

    def serialize_object(self, db_object, session):
        pass


def split_list(list_to_split, split_index):
    return list_to_split[:split_index], list_to_split[split_index:]


class Indexer:
    """
    Handle the indexing of the DB to ES.

    This object contains a number listeners.
    First a list of the changes to be made will be kept.
    In case of a commit, these changes will also be executed.
    """

    def __init__(
        self,
        settings,
        index_operation,
        index_operation_name,
        cls,
        index_attachments=False,
        max_items_per_job=10000,
    ):
        self.sessions = set()
        self.index_operation = index_operation
        self.index_operation_name = index_operation_name
        self._register_event_listeners(cls)
        self.settings = settings
        self.cls_name = cls.__name__
        self.index_attachments = index_attachments
        self.items_per_job = max_items_per_job

    def _register_event_listeners(self, cls):
        """
        Register event listeners.

        :param cls: DB class
        """
        event.listen(cls, "after_insert", self._new_listener)
        event.listen(cls, "after_update", self._update_listener)
        event.listen(cls, "after_delete", self._delete_listener)

    @staticmethod
    def _update_listener(mapper, connection, target):
        _add_to_session_list(target, operation="UPDATE")

    @staticmethod
    def _new_listener(mapper, connection, target):
        _add_to_session_list(target, operation="ADD")

    @staticmethod
    def _delete_listener(mapper, connection, target):
        _add_to_session_list(target, operation="REMOVE")

    def register_session(self, session, redis=None):
        session.redis = redis
        session.index_new = session.index_new if hasattr(session, "index_new") else {}
        session.index_new[self.cls_name] = set()
        session.index_dirty = (
            session.index_dirty if hasattr(session, "index_dirty") else {}
        )
        session.index_dirty[self.cls_name] = set()
        session.index_deleted = (
            session.index_deleted if hasattr(session, "index_deleted") else {}
        )
        session.index_deleted[self.cls_name] = set()
        self.sessions.add(session)
        event.listen(session, "after_commit", self.after_commit_listener)
        event.listen(session, "after_rollback", self.after_rollback_listener)

    def after_commit_listener(self, session):
        """
        Process the changes.

        All new or changed items are now indexed.
        All deleted items are now removed from the index.
        """
        log.info("Committing indexing orders for session %s" % session)
        try:
            if session.redis is not None:
                self.send_index_jobs(session)
            else:
                log.info(
                    "Redis not found, "
                    "falling back to indexing synchronously without redis"
                )
                index_args = [
                    session.index_new[self.cls_name],
                    session.index_dirty[self.cls_name],
                    session.index_deleted[self.cls_name],
                    self.settings,
                ]
                if self.index_attachments:
                    index_args.append(True)
                self.index_operation(*index_args)
            session.index_new[self.cls_name].clear()
            session.index_dirty[self.cls_name].clear()
            session.index_deleted[self.cls_name].clear()
        except AttributeError:
            log.warning(
                "Trying to commit indexing orders, but indexing sets are not present."
            )

    def send_index_jobs(self, session):
        remaining_new = list(session.index_new[self.cls_name])
        remaining_dirty = list(session.index_dirty[self.cls_name])
        remaining_deleted = list(session.index_deleted[self.cls_name])

        job_counter = 0
        job_reference = session.info.get("job_reference", str(uuid.uuid4()))

        while remaining_new or remaining_dirty or remaining_deleted:
            new_items, remaining_new = split_list(remaining_new, self.items_per_job)
            dirty_items, remaining_dirty = split_list(
                remaining_dirty, self.items_per_job - len(new_items)
            )
            deleted_items, remaining_deleted = split_list(
                remaining_deleted,
                self.items_per_job - len(new_items) - len(dirty_items),
            )

            job_id = f"{job_reference}_{job_counter}_{self.cls_name}"
            job_counter += 1

            queue_job(
                queue_name=self.settings["redis.queue_name"],
                delegate=self.index_operation_name,
                delegate_args=[new_items, dirty_items, deleted_items, self.settings],
                enqueue_kwargs={
                    "at_front": self.index_attachments,
                    "job_id": f"{job_id}_indexatie",
                },
                redis=session.redis,
            )
            if self.index_attachments:
                queue_job(
                    redis=session.redis,
                    queue_name=self.settings["redis.queue_name"],
                    delegate=self.index_operation_name,
                    delegate_args=[new_items, dirty_items, [], self.settings, True],
                    enqueue_kwargs={"job_id": f"{job_id}_indexatie_attachments"},
                )

    def after_rollback_listener(self, session):
        """
        Rollback of the transaction, undo the indexes.

        If our transaction is terminated, we will reset the
        indexing assignments.
        """
        log.info("Removing indexing orders.")
        try:
            session.index_new[self.cls_name].clear()
            session.index_dirty[self.cls_name].clear()
            session.index_deleted[self.cls_name].clear()
        except (AttributeError, KeyError):
            log.warning(
                "Trying to remove indexing orders, but indexing sets are not present."
            )

    def remove_session(self, session):
        """
        Remove a session from the indexer.

        :param sqlalchemy.session.Session session: Database session to remove
        """
        try:
            del session.redis
        except AttributeError:
            pass
        try:
            del session.index_new[self.cls_name]
            del session.index_dirty[self.cls_name]
            del session.index_deleted[self.cls_name]
        except (AttributeError, KeyError):
            log.warning("Removing a session that has no indexing sets.")
        self.sessions.remove(session)


def _add_to_session_list(target, operation):
    session = object_session(target)
    try:
        if operation == "ADD":
            session.index_new[target.__class__.__name__].add(target.id)
        elif operation == "UPDATE":
            session.index_dirty[target.__class__.__name__].add(target.id)
        elif operation == "REMOVE":
            session.index_deleted[target.__class__.__name__].add(target.id)
        log.info("%s: %s %s from index", operation, target, target.id)
    except (AttributeError, KeyError):
        log.warning(
            "Trying to register a %s for indexing %s, "
            "but indexing sets are not present.",
            target,
            operation,
        )
