import asyncio
import itertools
import json
import logging
from datetime import date
from datetime import datetime
from typing import Any
from typing import Mapping

import httpx
from elasticsearch8 import NotFoundError
from fastapi import FastAPI
from geojson import mapping
from oe_geoutils.utils import convert_geojson_to_geometry
from oe_geoutils.utils import convert_wktelement_to_geojson
from oe_geoutils.utils import epsg
from oe_geoutils.utils import get_srid_from_geojson
from oe_geoutils.utils import transform_projection
from oe_utils.search.searchengine import SearchEngine
from oe_utils.utils.db_utils import db_session
from oeauth.openid import OpenIDHelper
from pytz import timezone
from skosprovider.registry import Registry

from app.core.config import Settings as AppSettings
from app.core.config import get_settings
from app.models import Plan
from app.search.indexer import Indexer
from app.skos import fill_registry

log = logging.getLogger(__name__)
timezone_CET = timezone("CET")


def _prepare_settings_for_index(
    settings: AppSettings | Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build a settings dictionary with the legacy keys expected by the search/index
    code while supporting values loaded via the FastAPI `Settings` object.
    """
    if isinstance(settings, Mapping):
        combined: dict[str, Any] = dict(settings)
    elif hasattr(settings, "model_dump"):
        base_settings = settings.model_dump()
        extra_settings = getattr(settings, "model_extra", {})
        combined = dict(extra_settings)
        combined.update(base_settings)
    else:
        raise TypeError(
            "Unsupported settings type; provide a Mapping or Settings instance."
        )

    prepared: dict[str, Any] = {}

    for key, value in combined.items():
        if value is None:
            continue
        prepared[key] = value
        lower_key = key.lower()
        prepared.setdefault(lower_key, value)
        prepared.setdefault(lower_key.replace("_", "."), value)
        upper_key = key.upper()
        prepared.setdefault(upper_key, value)
        prepared.setdefault(upper_key.replace(".", "_"), value)
        prepared.setdefault(lower_key.replace(".", "_"), value)

    if "sqlalchemy.url" not in prepared:
        database_url = (
            prepared.get("DATABASE_URL")
            or prepared.get("database.url")
            or prepared.get("sqlalchemy_url")
        )
        if database_url:
            prepared["sqlalchemy.url"] = database_url

    prepared.setdefault("redis.max_connections", 1)

    return prepared


def _create_openid_helper(settings: Mapping[str, Any]) -> OpenIDHelper:
    def _require(key: str) -> Any:
        try:
            return settings[key]
        except KeyError as exc:
            raise KeyError(
                f"Missing required setting '{key}' for OpenIDHelper"
            ) from exc

    cache_kwargs = {
        "cache.backend": settings.get("oeauth.cache.backend"),
        "cache.arguments.host": settings.get("oeauth.cache.arguments.host"),
        "cache.arguments.redis.expiration.time": settings.get(
            "oeauth.cache.arguments.redis.expiration.time"
        ),
        "cache.arguments.distributed_lock": settings.get(
            "oeauth.cache.arguments.distributed_lock"
        ),
        "cache.arguments.thread.local.lock": settings.get(
            "oeauth.cache.arguments.thread.local.lock"
        ),
        "cache.arguments.lock.timeout": settings.get(
            "oeauth.cache.arguments.lock.timeout"
        ),
        "cache.expiration.time": settings.get("oeauth.cache.expiration.time"),
    }
    filtered_cache_kwargs = {
        key: value for key, value in cache_kwargs.items() if value is not None
    }

    return OpenIDHelper(
        client_id=_require("oeauth.client_id"),
        client_secret=_require("oeauth.client_secret"),
        systemuser_secret=_require("oeauth.systemuser_secret"),
        keycloak_public_key=settings.get("oeauth.keycloak_public_key"),
        **filtered_cache_kwargs,
    )


def encode_beheersplan(obj):
    if isinstance(obj, date) or isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return str(obj.decode(encoding="UTF-8"))
    raise TypeError(repr(obj) + " is not JSON serializable")


def beheersplan_to_es_dict(beheersplan, open_id_helper, skos_registry):
    plantype_naam = ""
    if beheersplan.plantype:
        plantpes_provider = skos_registry.get_provider("PLANTYPES")
        concept = plantpes_provider.get_by_uri(beheersplan.plantype.concept_uri)
        if concept:
            plantype_naam = concept.label().label

    async def fetch_aanduidingsobjecttype(erfgoedobject, skos_registry, open_id_helper):
        headers = {
            "Authorization": f"Bearer {open_id_helper.get_system_token()}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.get(erfgoedobject.erfgoedobject_id, headers=headers)
            if response.is_redirect:
                redirect_url = response.headers.get("location")
                if redirect_url:
                    response = await client.get(redirect_url, headers=headers)
            response.raise_for_status()
            aanduidingsobject = response.json()
        ao_skos_provider = skos_registry.get_provider("AANDUIDINGSTYPES")
        ao_type_concept = ao_skos_provider.get_by_uri(aanduidingsobject["type"]["uri"])
        return {
            "id": ao_type_concept.id,
            "uri": ao_type_concept.uri,
            "label": ao_type_concept.label().label,
        }

    async def fetch_aanduidingsobjecttypes(beheersplan, skos_registry, open_id_helper):
        erfgoedobjecten = beheersplan.erfgoedobjecten
        results = []
        slice_size = 50
        for i in range(0, len(erfgoedobjecten), slice_size):
            slice_objs = erfgoedobjecten[i : i + slice_size]
            batch = await asyncio.gather(
                *[
                    fetch_aanduidingsobjecttype(
                        erfgoedobject, skos_registry, open_id_helper
                    )
                    for erfgoedobject in slice_objs
                ]
            )
            results.extend(batch)
        return results

    aanduidingsobjecttypes = asyncio.run(
        fetch_aanduidingsobjecttypes(beheersplan, skos_registry, open_id_helper)
    )

    data = {
        "id": beheersplan.id,
        "onderwerp": beheersplan.onderwerp,
        "startdatum": (
            beheersplan.startdatum.isoformat()
            if beheersplan.startdatum is not None
            else None
        ),
        "einddatum": (
            beheersplan.einddatum.isoformat()
            if beheersplan.einddatum is not None
            else None
        ),
        "datum_goedkeuring": (
            beheersplan.datum_goedkeuring.isoformat()
            if beheersplan.datum_goedkeuring
            else None
        ),
        "beheerscommissie": beheersplan.beheerscommissie,
        "erfgoedobjecten": [e.erfgoedobject_id for e in beheersplan.erfgoedobjecten],
        "aanduidingsobjecttypes": aanduidingsobjecttypes,
        "plantype": beheersplan.plantype.concept_uri if beheersplan.plantype else "",
        "plantype_naam": plantype_naam,
        "systemfields": {
            "created_at": (
                beheersplan.created_at.isoformat()
                if beheersplan.created_at is not None
                else None
            ),
            "updated_at": (
                beheersplan.updated_at.isoformat()
                if beheersplan.updated_at is not None
                else None
            ),
        },
        "gemeenten": [
            {
                "niscode": element.gemeente_niscode,
                "naam": element.gemeente_naam,
            }
            for element in beheersplan.locatie_elementen
        ],
        "provincies": [
            {"niscode": element.provincie_niscode, "naam": element.provincie_naam}
            for element in beheersplan.locatie_elementen
        ],
        "status": {
            "datum": (
                beheersplan.status.datum.isoformat()
                if beheersplan.status
                else datetime.now(tz=timezone_CET).isoformat()
            ),
            "aanpasser_uri": (
                beheersplan.status.aanpasser_uri
                if beheersplan.status
                else "https://id.erfgoed.net/actoren/501"
            ),
            "aanpasser_omschrijving": (
                beheersplan.status.aanpasser_omschrijving
                if beheersplan.status
                else "Onroerend Erfgoed"
            ),
            "status": beheersplan.status.status.id if beheersplan.status else 0,
            "actief": beheersplan.status.actief if beheersplan.status else False,
        },
        # "acls": generate_plan_acls_es(beheersplan),
    }
    if beheersplan.geometrie is not None:
        geo_json = convert_wktelement_to_geojson(beheersplan.geometrie)
        data["geometrie"] = transform_contour_to_wsg84(geo_json)
    return data


def transform_contour_to_wsg84(contour):
    shape = convert_geojson_to_geometry(contour)
    shape = transform_projection(
        shape,
        epsg(get_srid_from_geojson(contour), True),
        epsg(4326, True),  # WSG 84
    )
    shape = shape.buffer(0)
    return mapping.to_mapping(shape)


def index_beheersplan(
    searchengine,
    session,
    _id,
    open_id_helper,
    skos_registry,
    settings=None,
):
    beheersplan = session.query(Plan).get(_id)
    if not beheersplan:
        log.warning("I was ordered to index beheersplan %d, but I can't find it." % _id)
        return

    beheersplan_json = beheersplan_to_es_dict(
        beheersplan, open_id_helper, skos_registry
    )
    searchengine.add_to_index(beheersplan.id, json.dumps(beheersplan_json))


def delete_beheersplan_from_index(search_engine, _id):
    try:
        search_engine.remove_from_index(_id)
    except NotFoundError:
        log.warning(
            "Geprobeerd een beheersplan te vewijderen uit de ES index "
            "dat niet aanwezig was: %d" % _id
        )


def index_operation(index_new, index_dirty, index_deleted, settings):
    log.info("starting index operation")
    prepared_settings = (
        settings
        if isinstance(settings, dict)
        else _prepare_settings_for_index(settings)
    )
    skos_registry = Registry()
    fill_registry(skos_registry, settings)
    # init_caches(settings)
    with db_session(settings) as dbsession:
        search_engine = SearchEngine(
            prepared_settings["ELASTICSEARCH_URL"],
            prepared_settings["SEARCHENGINE.INDEX"],
            es_version="8",
            api_key=prepared_settings.get("ELASTICSEARCH_API_KEY"),
        )
        open_id_helper = _create_openid_helper(prepared_settings)
        for n in itertools.chain(index_new, index_dirty):
            index_beheersplan(
                search_engine,
                dbsession,
                n,
                open_id_helper,
                skos_registry,
                prepared_settings,
            )
        for d in index_deleted:
            delete_beheersplan_from_index(search_engine, d)


def setup_indexer(
    app: FastAPI, settings: AppSettings | Mapping[str, Any] | None = None
) -> Indexer:
    configuration = _prepare_settings_for_index(settings or get_settings())
    indexer = Indexer(
        configuration,
        index_operation,
        "app.search.index.index_operation",
        Plan,
    )
    app.state.indexer = indexer

    return indexer
