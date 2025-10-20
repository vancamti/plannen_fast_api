from __future__ import annotations

import logging
from datetime import date
from datetime import datetime
from typing import Any
from typing import ClassVar

from geoalchemy2 import Geometry
from oe_geoutils.utils import convert_wktelement_to_geojson
from pytz import timezone
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app import schemas
from app.constants import SETTINGS
from app.db.base import Base
from app.models import enums

log = logging.getLogger(__name__)
timezone_CET = timezone("CET")

Base.registry.type_annotation_map.update({enums.Status: Enum(enums.Status)})


class Plan(Base):
    """Stelt één plan voor."""

    __tablename__ = "plannen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    onderwerp: Mapped[str | None] = mapped_column(String(250))
    datum_goedkeuring: Mapped[date | None] = mapped_column(Date)
    startdatum: Mapped[date | None] = mapped_column(Date)
    einddatum: Mapped[date | None] = mapped_column(Date)
    beheerscommissie: Mapped[bool | None] = mapped_column(Boolean)
    geometrie: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=31370)
    )

    relaties: Mapped[list[PlanRelatie]] = relationship(
        "PlanRelatie",
        foreign_keys="PlanRelatie.van_id",
        cascade="all, delete-orphan",
        back_populates="van",
    )
    relaties_naar: Mapped[list[PlanRelatie]] = relationship(
        "PlanRelatie",
        foreign_keys="PlanRelatie.naar_id",
        cascade="all, delete-orphan",
        back_populates="naar",
    )
    statussen: Mapped[list[PlanStatus]] = relationship(
        "PlanStatus",
        cascade="all, delete-orphan",
        back_populates="plan",
    )
    concepten: Mapped[list[PlanConcept]] = relationship(
        "PlanConcept",
        cascade="all, delete-orphan",
        back_populates="plan",
    )
    bestanden: Mapped[list[PlanBestand]] = relationship(
        "PlanBestand",
        cascade="all, delete-orphan",
        back_populates="plan",
        order_by="PlanBestand.id",
    )
    erfgoedobjecten: Mapped[list[PlanErfgoedobject]] = relationship(
        "PlanErfgoedobject",
        cascade="all, delete-orphan",
        back_populates="plan",
    )
    locatie_elementen: Mapped[list[LocatieElement]] = relationship(
        "LocatieElement",
        cascade="all, delete-orphan",
        back_populates="plan",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

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
    # def plantype(self) -> PlanConcept | None:
    #     return next((c for c in self.concepten if c.plankenmerk.id == "plantypes"), None)
    #
    # def filter_relaties(self, type_: str) -> list[PlanRelatie]:
    #     """Filter de relaties van een plan volgens type."""
    #     return [relatie for relatie in self.relaties if relatie.relatietype.id == type_]
    #
    @hybrid_property
    def status(self) -> PlanStatus | None:
        session = Session.object_session(self)
        if session is None:
            return None

        stmt = (
            select(PlanStatus)
            .filter_by(plan_id=self.id)
            .order_by(PlanStatus.datum.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()

    # def before_flush_new(self, request, session: Session) -> None:
    #     now = datetime.now(tz=timezone_CET)
    #     if session.actor_uri:
    #         log.debug("Adding info on actor_uri %s to plan.", session.actor_uri)
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
    #         plan_status = PlanStatus(status=status, datum=now)
    #         if session.actor_uri:
    #             plan_status.aanpasser_uri = session.actor_uri
    #         if session.actor_omschrijving:
    #             plan_status.aanpasser_omschrijving = session.actor_omschrijving
    #         self.statussen.append(plan_status)
    #
    # def before_flush_dirty(self, request, session: Session) -> None:
    #     now = datetime.now(tz=timezone_CET)
    #     self.updated_at = now
    #     if session.actor_uri:
    #         self.updated_by_uri = session.actor_uri
    #     if session.actor_omschrijving:
    #         self.updated_by_description = session.actor_omschrijving

    def self(self) -> str:
        return SETTINGS["PLANNEN_URI"]

    def to_detail_model(self) -> schemas.PlanResponse:
        detail = schemas.PlanResponse.model_construct(
            id=self.id,
            onderwerp=self.onderwerp,
            datum_goedkeuring=self.datum_goedkeuring,
            startdatum=self.startdatum,
            einddatum=self.einddatum,
            beheerscommissie=self.beheerscommissie,
            geometrie=schemas.Geometrie(
                **convert_wktelement_to_geojson(self.geometrie)
            ),
            locatie_elementen=[],
            plantype={},
            relaties=[],
            actief=False,
            status=[],
            statussen=[],
        )

        return detail


class Relatietype(Base):
    """Het type van een relatie."""

    __tablename__ = "relatietypes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type: Mapped[str | None] = mapped_column(String(255))
    inverse: Mapped[str | None] = mapped_column(String(32))


class PlanRelatie(Base):
    """Houdt een relatie bij tussen twee plannen."""

    __tablename__ = "planrelaties"

    van_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plannen.id"),
        primary_key=True,
    )
    relatietype_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("relatietypes.id"),
        primary_key=True,
    )
    naar_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plannen.id"),
        primary_key=True,
    )

    relatietype: Mapped[Relatietype] = relationship("Relatietype")
    naar: Mapped[Plan] = relationship(
        "Plan",
        foreign_keys="PlanRelatie.naar_id",
        back_populates="relaties_naar",
        overlaps="relaties",
    )
    van: Mapped[Plan] = relationship(
        "Plan",
        foreign_keys="PlanRelatie.van_id",
        back_populates="relaties",
        overlaps="relaties_naar",
    )


class PlanErfgoedobject(Base):
    """Stelt een koppeling tussen een plan en een erfgoedobject voor."""

    __tablename__ = "plannen_erfgoedobjecten"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plannen.id"),
        nullable=False,
    )
    erfgoedobject_id: Mapped[str] = mapped_column(String, nullable=False)
    plan: Mapped[Plan] = relationship("Plan", back_populates="erfgoedobjecten")


class PlanStatus(Base):
    """Stelt een koppeling tussen een plan en zijn status voor."""

    __tablename__ = "plannen_statussen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plannen.id"),
        nullable=False,
    )
    status: Mapped[enums.Status] = mapped_column()
    datum: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    aanpasser_uri: Mapped[str] = mapped_column(
        String(255),
        default="https://id.erfgoed.net/actoren/501",
        nullable=False,
    )
    aanpasser_omschrijving: Mapped[str] = mapped_column(
        String(255),
        default="Onroerend Erfgoed",
        nullable=False,
    )
    opmerkingen: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[Plan] = relationship("Plan", back_populates="statussen")

    @hybrid_property
    def actief(self) -> bool:
        return self.status.id > 50


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


class PlanBestand(Base):
    """Stelt een koppeling tussen een plan en een bestand voor."""

    __tablename__ = "plannen_bestanden"

    temporary_storage_key: ClassVar[str | None] = None

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plannen.id"))
    mime: Mapped[str | None] = mapped_column(String(250))
    naam: Mapped[str | None] = mapped_column(String(250))

    plan: Mapped[Plan] = relationship("Plan", back_populates="bestanden")
    bestandssoort: Mapped[enums.Bestandssoort] = mapped_column()

    @hybrid_property
    def bestand(self) -> str:
        return ""

    @bestand.setter
    def bestand(self, value: str) -> None:
        self.mime = value


#
# def after_flush_new(self, request, session: Session) -> None:
#     if self.temporary_storage_key is not None:
#         content_manager = request.registry.content_manager
#         content_manager.copy_temp_content(self.temporary_storage_key, self.plan_id, self.id)
#
# def after_flush_dirty(self, request, session: Session) -> None:
#     if self.temporary_storage_key is not None:
#         content_manager = request.registry.content_manager
#         content_manager.copy_temp_content(self.temporary_storage_key, self.plan_id, self.id)
#
# def persistent_to_deleted(self, request, session: Session) -> None:
#     content_manager = request.registry.content_manager
#     try:
#         content_manager.remove_content(self.plan_id, self.id)
#     except InvalidStateException as exc:
#         if exc.status_code != 404:
#             raise


class PlanConcept(Base):
    """Stelt een koppeling tussen een plan en een concept voor."""

    __tablename__ = "plannen_concepten"

    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plannen.id"),
        primary_key=True,
    )
    plan_kenmerk_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("plankenmerken.id"),
        primary_key=True,
        nullable=False,
    )
    concept_uri: Mapped[str] = mapped_column(String(100), primary_key=True)

    plan: Mapped[Plan] = relationship("Plan", back_populates="concepten")
    plankenmerk: Mapped[Plankenmerk] = relationship(
        "Plankenmerk", back_populates="concepten"
    )

    __table_args__ = (
        Index(
            "plan_scheme_concept_idx",
            "plan_id",
            "plan_kenmerk_id",
            "concept_uri",
            unique=True,
        ),
    )


# def label(self, request) -> str:
#     """Zoek een label voor dit concept."""
#     prefix, scheme_id, concept_id = self.concept_uri.rsplit("/", 2)
#     provider = request.skos_registry.get_provider(scheme_id.upper())
#     concept = provider.get_by_id(concept_id)
#     return concept.label() if concept else ""


class Plankenmerk(Base):
    """Stelt een kenmerk van een plan voor."""

    __tablename__ = "plankenmerken"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kenmerk: Mapped[str | None] = mapped_column(String(255))
    concepten: Mapped[list[PlanConcept]] = relationship(
        "PlanConcept", back_populates="plankenmerk"
    )


# class Bestandssoort(Base):
#     """Stelt de soort van een bestand voor."""
#
#     __tablename__ = "bestandssoorten"
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     soort: Mapped[str | None] = mapped_column(String(100))
#
#     bestanden: Mapped[list[PlanBestand]] = relationship(
#         "PlanBestand", back_populates="bestandssoort"
#     )


class FeedEntry(Base):
    __tablename__ = "feedentries"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uri: Mapped[str] = mapped_column(String, nullable=False)
    actie: Mapped[str | None] = mapped_column(String(10))
    datum: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(tz=timezone_CET), nullable=False
    )
    onderwerp: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(String(255))


class LocatieElement(Base):
    __tablename__ = "locatie_elementen"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str | None] = mapped_column(String(250))
    resource_object_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("plannen.id")
    )
    provincie_niscode: Mapped[str | None] = mapped_column(String)
    provincie_naam: Mapped[str | None] = mapped_column(String(50))
    gemeente_niscode: Mapped[str | None] = mapped_column(String)
    gemeente_naam: Mapped[str | None] = mapped_column(String(255))

    plan: Mapped[Plan | None] = relationship("Plan", back_populates="locatie_elementen")

    __mapper_args__ = {
        "polymorphic_identity": "https://id.erfgoed.net/vocab/ontology#LocatieElement",
        "polymorphic_on": type,
    }


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
    # "PlanRelatie",
    # "PlanErfgoedobject",
    # "PlanStatus",
    # "Status",
    # "PlanBestand",
    # "PlanConcept",
    # "Plankenmerk",
    # "Bestandssoort",
    # "FeedEntry",
    # "LocatieElement",
    # "session_before_flush",
    # "session_after_flush",
    # "session_persistent_to_deleted",
    # "register_listeners",
]
