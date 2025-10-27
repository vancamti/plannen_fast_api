import asyncio
import itertools
import json
import logging
from datetime import date
from datetime import datetime

import httpx
from elasticsearch8 import NotFoundError
from geojson import mapping
from oe_geoutils.utils import convert_geojson_to_geometry
from oe_geoutils.utils import convert_wktelement_to_geojson
from oe_geoutils.utils import epsg
from oe_geoutils.utils import get_srid_from_geojson
from oe_geoutils.utils import transform_projection
from oe_utils.search.indexer import Indexer
from oe_utils.search.searchengine import SearchEngine
from oe_utils.utils import dict_utils
from oe_utils.utils.db_utils import db_session
from oeauth import parse_settings
from oeauth.openid import OpenIDHelper
from pytz import timezone
from skosprovider.registry import Registry

from app.models import Plan
from app.skos import fill_registry

log = logging.getLogger(__name__)
timezone_CET = timezone("CET")

index_settings_keys = {
    "sqlalchemy.url",
    "administratievegrenzen.url",
    "idservice.url",
}

index_settings_key_prefixes = {
    "oeauth.",
    "redis.",
    "searchengine.",
    "storageprovider.",
    "skos.",
    "thesaurus.",
    "idservice.url",
}


def _prepare_settings_for_index(settings):
    settings = dict_utils.filter_flat_dict(
        settings,
        filter_prefixes=index_settings_key_prefixes,
        filter_keys=index_settings_keys,
        exclude_keys=["redis.sessions.client_callable"],
        exclude_suffixes=[".connection_pool"],
    )
    settings.update({"redis.max_connections": 1})

    return settings


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
            response = await client.get(
                erfgoedobject.erfgoedobject_id, headers=headers
            )
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
            slice_objs = erfgoedobjecten[i:i + slice_size]
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
    skos_registry = Registry()
    fill_registry(skos_registry, settings)
    # init_caches(settings)
    with db_session(settings) as dbsession:
        search_engine = SearchEngine(
            settings["ELASTICSEARCH_URL"],
            settings["ELASTICSEARCH_URL"],
            es_version="8",
            api_key=settings["ELASTICSEARCH_API_KEY"],
        )
        kwargs = parse_settings(settings)
        open_id_helper = OpenIDHelper(**kwargs)
        for n in itertools.chain(index_new, index_dirty):
            index_beheersplan(
                search_engine,
                dbsession,
                n,
                open_id_helper,
                skos_registry,
                settings,
            )
        for d in index_deleted:
            delete_beheersplan_from_index(search_engine, d)


def includeme(config):
    config.registry.indexer = Indexer(
        _prepare_settings_for_index(config.registry.settings),
        index_operation,
        "plannen.search.index.index_operation",
        Plan,
    )
