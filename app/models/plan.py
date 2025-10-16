from __future__ import annotations

import logging
from datetime import date

from pytz import timezone
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.base import Base

log = logging.getLogger(__name__)
timezone_CET = timezone("CET")


class Plan(Base):
    """Stelt één beheersplan voor."""

    __tablename__ = "plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    onderwerp: Mapped[str | None] = mapped_column(String(250))
    datum_goedkeuring: Mapped[date | None] = mapped_column(Date)
    startdatum: Mapped[date | None] = mapped_column(Date)
    einddatum: Mapped[date | None] = mapped_column(Date)
    beheerscommissie: Mapped[bool | None] = mapped_column(Boolean)
    # geometrie: Mapped[Any] = mapped_column(Geometry(geometry_type="MULTIPOLYGON", srid=31370))
    #
    # relaties: Mapped[list[BeheersplanRelatie]] = relationship(
    #     "BeheersplanRelatie",
    #     foreign_keys="BeheersplanRelatie.van_id",
    #     cascade="all, delete-orphan",
    #     back_populates="van",
    # )
    # relaties_naar: Mapped[list[BeheersplanRelatie]] = relationship(
    #     "BeheersplanRelatie",
    #     foreign_keys="BeheersplanRelatie.naar_id",
    #     cascade="all, delete-orphan",
    #     back_populates="naar",
    # )
    # statussen: Mapped[list[BeheersplanStatus]] = relationship(
    #     "BeheersplanStatus",
    #     cascade="all, delete-orphan",
    #     back_populates="beheersplan",
    # )
    # concepten: Mapped[list[BeheersplanConcept]] = relationship(
    #     "BeheersplanConcept",
    #     cascade="all, delete-orphan",
    #     back_populates="beheersplan",
    # )
    # bestanden: Mapped[list[BeheersplanBestand]] = relationship(
    #     "BeheersplanBestand",
    #     cascade="all, delete-orphan",
    #     back_populates="beheersplan",
    #     order_by="BeheersplanBestand.id",
    # )
    # erfgoedobjecten: Mapped[list[BeheersplanErfgoedobject]] = relationship(
    #     "BeheersplanErfgoedobject",
    #     cascade="all, delete-orphan",
    #     back_populates="beheersplan",
    # )
    # locatie_elementen: Mapped[list[LocatieElement]] = relationship(
    #     "LocatieElement",
    #     cascade="all, delete-orphan",
    #     back_populates="beheersplan",
    # )
    #
    # created_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     default=func.now(),
    #     nullable=False,
    # )
    # created_by_uri: Mapped[str] = mapped_column(
    #     String(255),
    #     default="https://id.erfgoed.net/actoren/501",
    #     nullable=False,
    # )
    # created_by_description: Mapped[str] = mapped_column(
    #     String(255),
    #     default="Onroerend Erfgoed",
    #     nullable=False,
    # )
    # updated_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     default=func.now(),
    #     nullable=False,
    # )
    # updated_by_uri: Mapped[str] = mapped_column(
    #     String(255),
    #     default="https://id.erfgoed.net/actoren/501",
    #     nullable=False,
    # )
    # updated_by_description: Mapped[str] = mapped_column(
    #     String(255),
    #     default="Onroerend Erfgoed",
    #     nullable=False,
    # )
    #
    # @hybrid_property
    # def plantype(self) -> BeheersplanConcept | None:
    #     return next((c for c in self.concepten if c.beheersplankenmerk.id == "plantypes"), None)
    #
    # def filter_relaties(self, type_: str) -> list[BeheersplanRelatie]:
    #     """Filter de relaties van een beheersplan volgens type."""
    #     return [relatie for relatie in self.relaties if relatie.relatietype.id == type_]
    #
    # @hybrid_property
    # def status(self) -> BeheersplanStatus | None:
    #     session = Session.object_session(self)
    #     if session is None:
    #         return None
    #
    #     stmt = (
    #         select(BeheersplanStatus)
    #         .filter_by(beheersplan_id=self.id)
    #         .order_by(BeheersplanStatus.datum.desc())
    #         .limit(1)
    #     )
    #     return session.scalars(stmt).first()

    # def before_flush_new(self, request, session: Session) -> None:
    #     now = datetime.now(tz=timezone_CET)
    #     if session.actor_uri:
    #         log.debug("Adding info on actor_uri %s to beheersplan.", session.actor_uri)
    #
    #     self.created_at = now
    #     if session.actor_uri:
    #         self.created_by_uri = session.actor_uri
    #         self.updated_by_uri = session.actor_uri
    #     if session.actor_omschrijving:
    #         self.created_by_description = session.actor_omschrijving
    #         self.updated_by_description = session.actor_omschrijving
    #     self.updated_at = now
    #
    #     if len(self.statussen) == 0:
    #         status = session.get(Status, 10)
    #         if status is None:
    #             return
    #         beheersplan_status = BeheersplanStatus(status=status, datum=now)
    #         if session.actor_uri:
    #             beheersplan_status.aanpasser_uri = session.actor_uri
    #         if session.actor_omschrijving:
    #             beheersplan_status.aanpasser_omschrijving = session.actor_omschrijving
    #         self.statussen.append(beheersplan_status)
    #
    # def before_flush_dirty(self, request, session: Session) -> None:
    #     now = datetime.now(tz=timezone_CET)
    #     self.updated_at = now
    #     if session.actor_uri:
    #         self.updated_by_uri = session.actor_uri
    #     if session.actor_omschrijving:
    #         self.updated_by_description = session.actor_omschrijving


#
# class Relatietype(Base):
#     """Het type van een relatie."""
#
#     __tablename__ = "relatietypes"
#
#     id: Mapped[str] = mapped_column(String(32), primary_key=True)
#     type: Mapped[str | None] = mapped_column(String(255))
#     inverse: Mapped[str | None] = mapped_column(String(32))
#
#
# class BeheersplanRelatie(Base):
#     """Houdt een relatie bij tussen twee plannen."""
#
#     __tablename__ = "beheersplanrelaties"
#
#     van_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("beheersplannen.id"),
#         primary_key=True,
#     )
#     relatietype_id: Mapped[str] = mapped_column(
#         String(32),
#         ForeignKey("relatietypes.id"),
#         primary_key=True,
#     )
#     naar_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("beheersplannen.id"),
#         primary_key=True,
#     )
#
#     relatietype: Mapped[Relatietype] = relationship("Relatietype")
#     naar: Mapped[Plan] = relationship(
#         "Plan",
#         foreign_keys="BeheersplanRelatie.naar_id",
#         back_populates="relaties_naar",
#         overlaps="relaties",
#     )
#     van: Mapped[Plan] = relationship(
#         "Plan",
#         foreign_keys="BeheersplanRelatie.van_id",
#         back_populates="relaties",
#         overlaps="relaties_naar",
#     )
#
#
# class BeheersplanErfgoedobject(Base):
#     """Stelt een koppeling tussen een beheersplan en een erfgoedobject voor."""
#
#     __tablename__ = "beheersplannen_erfgoedobjecten"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     beheersplan_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("beheersplannen.id"),
#         nullable=False,
#     )
#     erfgoedobject_id: Mapped[str] = mapped_column(String, nullable=False)
#
#     beheersplan: Mapped[Plan] = relationship("Plan", back_populates="erfgoedobjecten")
#
#
# class BeheersplanStatus(Base):
#     """Stelt een koppeling tussen een beheersplan en zijn status voor."""
#
#     __tablename__ = "beheersplannen_statussen"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     beheersplan_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("beheersplannen.id"),
#         nullable=False,
#     )
#     status_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("statussen.id"),
#         nullable=False,
#     )
#     status: Mapped[Status] = relationship("Status")
#     datum: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
#     aanpasser_uri: Mapped[str] = mapped_column(
#         String(255),
#         default="https://id.erfgoed.net/actoren/501",
#         nullable=False,
#     )
#     aanpasser_omschrijving: Mapped[str] = mapped_column(
#         String(255),
#         default="Onroerend Erfgoed",
#         nullable=False,
#     )
#     opmerkingen: Mapped[str | None] = mapped_column(Text)
#
#     beheersplan: Mapped[Plan] = relationship("Plan", back_populates="statussen")

# def before_flush_new(self, request, session: Session) -> None:
#     if session.actor_uri:
#         log.debug("Adding info on actor %s to statussen.", session.actor_uri)
#     self.datum = datetime.now(tz=timezone_CET)
#     if session.actor_uri:
#         self.aanpasser_uri = session.actor_uri
#     if session.actor_omschrijving:
#         self.aanpasser_omschrijving = session.actor_omschrijving
#
#     @hybrid_property
#     def actief(self) -> bool:
#         return self.status.actief
#
#
# class Status(Base):
#     __tablename__ = "statussen"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     status: Mapped[str | None] = mapped_column(String(255))
#
#     @hybrid_property
#     def actief(self) -> bool:
#         return self.id > 50
#
#
# class BeheersplanBestand(Base):
#     """Stelt een koppeling tussen een beheersplan en een bestand voor."""
#
#     __tablename__ = "beheersplannen_bestanden"
#
#     temporary_storage_key: ClassVar[str | None] = None
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     beheersplan_id: Mapped[int] = mapped_column(Integer, ForeignKey("beheersplannen.id"))
#     bestandssoort_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bestandssoorten.id"))
#     mime: Mapped[str | None] = mapped_column(String(250))
#     naam: Mapped[str | None] = mapped_column(String(250))
#
#     beheersplan: Mapped[Plan] = relationship("Plan", back_populates="bestanden")
#     bestandssoort: Mapped[Bestandssoort | None] = relationship("Bestandssoort")
#
#     @hybrid_property
#     def bestand(self) -> str:
#         return ""
#
#     @bestand.setter
#     def bestand(self, value: str) -> None:
#         self.mime = value
#
# def after_flush_new(self, request, session: Session) -> None:
#     if self.temporary_storage_key is not None:
#         content_manager = request.registry.content_manager
#         content_manager.copy_temp_content(self.temporary_storage_key, self.beheersplan_id, self.id)
#
# def after_flush_dirty(self, request, session: Session) -> None:
#     if self.temporary_storage_key is not None:
#         content_manager = request.registry.content_manager
#         content_manager.copy_temp_content(self.temporary_storage_key, self.beheersplan_id, self.id)
#
# def persistent_to_deleted(self, request, session: Session) -> None:
#     content_manager = request.registry.content_manager
#     try:
#         content_manager.remove_content(self.beheersplan_id, self.id)
#     except InvalidStateException as exc:
#         if exc.status_code != 404:
#             raise

#
# class BeheersplanConcept(Base):
#     """Stelt een koppeling tussen een beheersplan en een concept voor."""
#
#     __tablename__ = "beheersplannen_concepten"
#
#     beheersplan_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("beheersplannen.id"),
#         primary_key=True,
#     )
#     beheersplan_kenmerk_id: Mapped[str] = mapped_column(
#         String(64),
#         ForeignKey("beheersplankenmerken.id"),
#         primary_key=True,
#         nullable=False,
#     )
#     concept_uri: Mapped[str] = mapped_column(String(100), primary_key=True)
#
#     beheersplan: Mapped[Plan] = relationship("Plan", back_populates="concepten")
#     beheersplankenmerk: Mapped[Beheersplankenmerk] = relationship("Beheersplankenmerk", back_populates="concepten")
#
#     __table_args__ = (
#         Index(
#             "beheersplan_scheme_concept_idx",
#             "beheersplan_id",
#             "beheersplan_kenmerk_id",
#             "concept_uri",
#             unique=True,
#         ),
#     )

# def label(self, request) -> str:
#     """Zoek een label voor dit concept."""
#     prefix, scheme_id, concept_id = self.concept_uri.rsplit("/", 2)
#     provider = request.skos_registry.get_provider(scheme_id.upper())
#     concept = provider.get_by_id(concept_id)
#     return concept.label() if concept else ""

#
# class Beheersplankenmerk(Base):
#     """Stelt een kenmerk van een beheersplan voor."""
#
#     __tablename__ = "beheersplankenmerken"
#
#     id: Mapped[str] = mapped_column(String(64), primary_key=True)
#     kenmerk: Mapped[str | None] = mapped_column(String(255))
#     concepten: Mapped[list[BeheersplanConcept]] = relationship("BeheersplanConcept", back_populates="beheersplankenmerk")
#
#
# class Bestandssoort(Base):
#     """Stelt de soort van een bestand voor."""
#
#     __tablename__ = "bestandssoorten"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     soort: Mapped[str | None] = mapped_column(String(100))
#
#     bestanden: Mapped[list[BeheersplanBestand]] = relationship("BeheersplanBestand", back_populates="bestandssoort")
#
#
# class FeedEntry(Base):
#     __tablename__ = "feedentries"
#     __table_args__ = {"sqlite_autoincrement": True}
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     uri: Mapped[str] = mapped_column(String, nullable=False)
#     actie: Mapped[str | None] = mapped_column(String(10))
#     datum: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(tz=timezone_CET), nullable=False)
#     onderwerp: Mapped[str | None] = mapped_column(String(255))
#     content: Mapped[str | None] = mapped_column(String(255))
#
#
# class LocatieElement(Base):
#     __tablename__ = "locatie_elementen"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     type: Mapped[str | None] = mapped_column(String(250))
#     resource_object_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("beheersplannen.id"))
#     provincie_niscode: Mapped[str | None] = mapped_column(String)
#     provincie_naam: Mapped[str | None] = mapped_column(String(50))
#     gemeente_niscode: Mapped[str | None] = mapped_column(String)
#     gemeente_naam: Mapped[str | None] = mapped_column(String(255))
#
#     beheersplan: Mapped[Plan | None] = relationship("Plan", back_populates="locatie_elementen")
#
#     __mapper_args__ = {
#         "polymorphic_identity": "https://id.erfgoed.net/vocab/ontology#LocatieElement",
#         "polymorphic_on": type,
#     }
#
#
# def _invoke(instance: Any, hook: str, request, session: Session) -> None:
#     """Call hook on instance when available."""
#     if hasattr(instance, hook):
#         getattr(instance, hook)(request, session)


# def session_before_flush(session: Session, request) -> None:
#     for instance in list(session.new):
#         _invoke(instance, "before_flush_new", request, session)
#     for instance in list(session.dirty):
#         _invoke(instance, "before_flush_dirty", request, session)
#     for instance in list(session.deleted):
#         _invoke(instance, "before_flush_deleted", request, session)
#     for instance in it.chain(session.new, session.dirty, session.deleted):
#         _invoke(instance, "before_flush", request, session)
#
#
# def session_after_flush(session: Session, request) -> None:
#     for instance in list(session.new):
#         _invoke(instance, "after_flush_new", request, session)
#     for instance in list(session.dirty):
#         _invoke(instance, "after_flush_dirty", request, session)
#     for instance in list(session.deleted):
#         _invoke(instance, "after_flush_deleted", request, session)
#     for instance in it.chain(session.new, session.dirty, session.deleted):
#         _invoke(instance, "after_flush", request, session)


# def session_persistent_to_deleted(session: Session, instance: Any, request) -> None:
#     _invoke(instance, "persistent_to_deleted", request, session)
#
#
# def register_listeners(session: Session, request) -> None:
#     event.listen(session, "before_flush", lambda *_: session_before_flush(session, request))
#     event.listen(session, "after_flush", lambda *_: session_after_flush(session, request))
#     event.listen(
#         session,
#         "persistent_to_deleted",
#         lambda _, instance: session_persistent_to_deleted(session, instance, request),
#     )


__all__ = [
    "Base",
    "Plan",
    # "Relatietype",
    # "BeheersplanRelatie",
    # "BeheersplanErfgoedobject",
    # "BeheersplanStatus",
    # "Status",
    # "BeheersplanBestand",
    # "BeheersplanConcept",
    # "Beheersplankenmerk",
    # "Bestandssoort",
    # "FeedEntry",
    # "LocatieElement",
    # "session_before_flush",
    # "session_after_flush",
    # "session_persistent_to_deleted",
    # "register_listeners",
]
