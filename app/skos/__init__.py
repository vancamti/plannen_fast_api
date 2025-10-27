import logging
import os

from skosprovider.providers import DictionaryProvider
from skosprovider.registry import Registry
from skosprovider.skos import ConceptScheme
from skosprovider.uri import UriPatternGenerator
from skosprovider_atramhasis.providers import AtramhasisProvider

log = logging.getLogger(__name__)


def plantypes_provider(settings):
    idservice_url = settings["idservice.url"]
    return DictionaryProvider(
        {"id": "PLANTYPES", "default_language": "nl"},
        [
            {
                "id": "OEB",
                "labels": [
                    {
                        "type": "prefLabel",
                        "language": "nl",
                        "label": "Onroerend Erfgoed Beheersplan",
                    }
                ],
            },
            {
                "id": "GEIB",
                "labels": [
                    {
                        "type": "prefLabel",
                        "language": "nl",
                        "label": "Geïntegreerd Beheersplan",
                    }
                ],
            },
            {
                "id": "OER",
                "labels": [
                    {
                        "type": "prefLabel",
                        "language": "nl",
                        "label": "Onroerenderfgoedrichtplan",
                    }
                ],
            },
        ],
        concept_scheme=ConceptScheme(uri=f"{idservice_url}/thesauri/plantypes"),
        uri_generator=UriPatternGenerator(f"{idservice_url}/thesauri/plantypes/%s"),
    )


def fill_registry(skos_registry, settings):
    atramhasis_provider_cache_config = {
        key[16:]: val  # 16: cuts off the prefix "skos.atramhasis."
        for key, val in settings.items()
        if key.startswith("skos.atramhasis.cache.")
    }
    if not atramhasis_provider_cache_config:
        log.info("No cache configuration set for atramhasis skosprovider")
        atramhasis_provider_cache_config = {"cache.backend": "dogpile.cache.null"}

    aanduidingstypes = AtramhasisProvider(
        {
            "id": "AANDUIDINGSTYPES",
            "default_language": "nl",
            "uri": os.path.join(settings["thesaurus.uri"], "aanduidingstypes"),
        },
        base_url=settings["thesaurus.url"],
        scheme_id="AANDUIDINGSTYPES",
        cache_config=atramhasis_provider_cache_config,
    )
    skos_registry.register_provider(aanduidingstypes)
    skos_registry.register_provider(plantypes_provider(settings))
    return skos_registry


def create_registry(request):
    registry = Registry(instance_scope="threaded_thread")
    settings = request.registry.settings
    return fill_registry(registry, settings)
