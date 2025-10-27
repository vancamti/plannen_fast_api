"""
Gebruik:

initialize_beheersplannen_es development.ini#plannen
- Maak een nieuwe elasticsearch mapping aan. Dit verwijdert alle documenten
  onder deze index.

Er zijn extra optionele parameters:
--reindex
  Indexeer ook alle items die in de databank aanwezig zijn.

--offset OFFSET
  Sla de eerste OFFSET items over. Deze parameter is enkel zinnig bij
  herindexeren en wordt genegeerd zonder --reindex.

--limit LIMIT
  Herindexeer enkel LIMIT items uit de database. Deze parameter is enkel
  zinnig bij herindexeren en wordt genegeerd zonder --reindex.

--id ID
  Herindexeer enkel het item uit de database met dit ID. Deze parameter is
  enkel zinnig bij herindexeren en wordt genegeerd zonder --reindex.
  Als je geen --index meegeeft, zal voor elk type deze ID worden gezocht.
  Meestal zal je --index willen gebruiken bij --id.

--batch-size BATCH_SIZE
  De maximum hoeveelheid items per keer wordt opgehaald uit de database en
  geherindexeert. Default 5000. Deze parameter is enkel zinnig bij herindexeren
  en wordt genegeerd zonder --reindex.
"""

import abc
import argparse
import contextlib
import logging
import os
import sys
import time
from copy import deepcopy
from datetime import timedelta

from dotenv import dotenv_values
from dotenv import load_dotenv
from elasticsearch8 import Elasticsearch
from oe_utils.scripts import create_indexing_argument_parser
from oe_utils.search.searchengine import SearchEngine
from oe_utils.utils.db_utils import db_session
from oeauth import parse_settings
from oeauth.openid import OpenIDHelper
from pyramid.paster import get_appsettings
from pyramid.paster import setup_logging
from skosprovider.registry import Registry
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from storageprovider.client import StorageProviderClient
from storageprovider.providers.minio import MinioProvider

from app import constants as c
from app.models import Plan
from app.search import index
from app.search.index import beheersplan_to_es_dict
from app.search.mapping.plannen import beheersplannen_index
from app.search.mapping.plannen import beheersplannen_mapping
from app.skos import fill_registry


log = logging.getLogger(__name__)
erfgoedobjecten = {}


def init_argparse(args):
    parser = create_indexing_argument_parser(["plannen"])
    parser.description = "initialize elasticsearch cli"
    parser.epilog = (
        "Voorbeeldgebruik: initialize_plannen_es development.ini#plannen --reindex"
    )
    parser.formatter_class = argparse.RawTextHelpFormatter
    parser.add_argument(
        "script_name",
        metavar="script_name",
        type=str,
        default="initialize_plannen_es",
        help="Naam van het te runnen script. \n"
        + "(Indien via pyramid ingeroepen default ingevuld.)",
    )
    parser.add_argument("configuratiebestand", type=str, help="ini config bestand")
    parser.add_argument(
        "--reindex",
        default=False,
        action="store_true",
        help="""indien parameter aanwezig: voer elasticsearch initalialisatie uit met
                        herindexering van data""",
    )
    parser.add_argument(
        "--batch-size",
        default=5000,
        type=int,
        help="De maximum hoeveelheid objecten per keer worden opgehaald uit de database.",
    )

    return parser.parse_args(args)

def load_settings(env_path=".env"):
    original_settings = dotenv_values(env_path)
    settings = deepcopy(original_settings)
    settings["sqlalchemy.url"] = settings["DATABASE_URL"]
    for key in original_settings.keys():
        settings[key.lower()] = settings[key]
    return settings

def fill_erfgoedobjecten(searchengine, plannen):
    eo_uris = set()
    for plan in plannen:
        eo_uris.update([eo.erfgoedobject_id for eo in plan.erfgoedobjecten])
    query = {"query": {"terms": {"uri": list(eo_uris)}}, "_source": ["uri", "type"]}
    response = searchengine.search(body=query, size=len(eo_uris))
    hits = response.get("hits", {}).get("hits", [])
    erfgoedobjecten.update({hit["_source"]["uri"]: hit["_source"] for hit in hits})



class Reindexer:
    def __init__(
        self,
        db_class,
        settings,
        setting_index_name,
        index_data,
        mapping,
    ):
        super().__init__()
        self.db_class = db_class
        self.searchengine = SearchEngine(
            settings["ELASTICSEARCH_URL"],
            settings[setting_index_name],
            es_version="8",
            api_key=settings["ELASTICSEARCH_API_KEY"],
        )
        provider = MinioProvider(
            server_url=settings.get("MINIO_ENDPOINT"),
            access_key=settings.get("MINIO_ACCESS_KEY"),
            secret_key=settings.get("MINIO_SECRET_KEY"),
            bucket_name=settings.get("MINIO_BUCKET_NAME"),
        )
        self.storageprovider = StorageProviderClient(provider)
        self.index_data = index_data
        self.mapping = mapping
        self.settings = settings
        self.inventaris_ao_searchengine = Elasticsearch(
            f'{settings["ELASTICSEARCH_URL"]}/inventaris_aanduidingsobjecten',
            api_key=settings["ELASTICSEARCH_API_KEY"],
        )

    @abc.abstractmethod
    def process_db_to_dict(self, plan, open_id_helper, skos_registry):
        pass

    def recreate_index(self):
        self.searchengine.remove_index()
        self.searchengine.create_index(data=beheersplannen_index)
        self.searchengine.add_mapping(beheersplannen_mapping)

    def reindex(
        self,
        session,
        open_id_helper,
        batch_size=5000,
        limit=None,
        offset=0,
        db_id=None,
        skos_registry=None,
    ):
        table_name = str(self.db_class.__table__.name).capitalize()
        log.info("%s herindexeren:", table_name)
        start_time = time.time()
        if limit:
            batch_size = min(batch_size, limit)
        query = self.build_query(batch_size, db_id, offset, session)
        db_objects = query.all()
        fill_erfgoedobjecten(self.inventaris_ao_searchengine, db_objects)
        index.get_uri_json = lambda uri, **kwargs: erfgoedobjecten.get(uri)
        while db_objects:
            next_offset = offset + len(db_objects)

            log.info("  Verwerken %s %s - %s", table_name, offset, next_offset)
            self.searchengine.bulk_add_to_index(
                (
                    self.process_db_to_dict(db_object, open_id_helper, skos_registry)
                    for db_object in db_objects
                ),
            )
            log.info(
                "  %s - %s OK. Gebruik '--offset %s' om te herstarten vanaf dit punt.",
                offset,
                next_offset,
                next_offset,
            )

            if limit:
                limit -= len(db_objects)
                batch_size = min(batch_size, limit)
                query = query.limit(batch_size)
            offset = next_offset
            query = query.offset(offset)
            db_objects = query.all()
            fill_erfgoedobjecten(self.inventaris_ao_searchengine, db_objects)

        log.info("%s done.", table_name)
        elapsed = time.time() - start_time
        log.info(f"Duration {str(timedelta(seconds=elapsed))}")

    def build_query(self, batch_size, db_id, offset, session):
        query = session.query(self.db_class).order_by(self.db_class.id)
        if db_id:
            query = query.filter(self.db_class.id == db_id)
        if offset:
            query = query.offset(offset)
        query = query.limit(batch_size)
        return query


class PlanReindexer(Reindexer):
    def __init__(self, settings):
        super().__init__(
            Plan,
            settings,
            "ELASTICSEARCH_INDEX",
            beheersplannen_index,
            beheersplannen_mapping,
        )

    def process_db_to_dict(self, plan, open_id_helper, skos_registry):
        return beheersplan_to_es_dict(
            plan, open_id_helper, skos_registry
        )


def main(argv=sys.argv):  # pragma NO COVER
    args = init_argparse(argv)
    settings = load_settings(args.configuratiebestand)
    settings["redis.max_connections"] = 1
    reindex = args.reindex
    open_id_helper = OpenIDHelper(
        client_id=c.settings.OEAUTH_CLIENT_ID,
        client_secret=c.settings.OEAUTH_CLIENT_SECRET,
        systemuser_secret=c.settings.OEAUTH_SYSTEMUSER_SECRET,
        keycloak_public_key=c.settings.OEAUTH_KEYCLOAK_PUBLIC_KEY,
        **{
            "cache.backend": c.settings.OEAUTH_CACHE_BACKEND,
            "cache.arguments.host": c.settings.OEAUTH_CACHE_ARGUMENTS_HOST,
            "cache.arguments.redis.expiration.time": c.settings.OEAUTH_CACHE_ARGUMENTS_REDIS_EXPIRATION_TIME,
            "cache.arguments.distributed_lock": c.settings.OEAUTH_CACHE_ARGUMENTS_DISTRIBUTED_LOCK,
            "cache.arguments.thread.local.lock": c.settings.OEAUTH_CACHE_ARGUMENTS_THREAD_LOCAL_LOCK,
            "cache.arguments.lock.timeout": c.settings.OEAUTH_CACHE_ARGUMENTS_LOCK_TIMEOUT,
            "cache.expiration.time": c.settings.OEAUTH_CACHE_EXPIRATION_TIME,
        }
    )
    reindexer = PlanReindexer(settings)
    skos_registry = Registry()
    fill_registry(skos_registry, settings)
    if args.id is None and args.offset is None:
        reindexer.recreate_index()
    if reindex:
        with db_session(settings) as session:
            reindexer.reindex(
                session,
                open_id_helper,
                batch_size=args.batch_size,
                limit=args.limit,
                offset=args.offset or 0,
                db_id=args.id,
                skos_registry=skos_registry,
            )


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv)
