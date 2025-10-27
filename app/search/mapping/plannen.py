beheersplannen_index = {
    "settings": {
        "index": {"codec": "best_compression"},
        "analysis": {
            "analyzer": {
                "string_lowercase": {
                    "type": "custom",
                    "tokenizer": "keyword",
                    "filter": ["lowercase"],
                }
            },
            "normalizer": {
                "keyword_lowercase": {
                    "type": "custom",
                    "char_filter": [],
                    "filter": ["lowercase"],
                }
            },
        },
    }
}

beheersplannen_mapping = {
    "properties": {
        "id": {"type": "integer"},
        "onderwerp": {
            "type": "text",
            "fields": {"raw": {"type": "keyword", "normalizer": "keyword_lowercase"}},
        },
        "aanduidingsobjecttypes": {
            "properties": {
                "id": {
                    "type": "long"
                },
                "naam": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "keyword_lowercase"
                        }
                    }
                },
                "uri": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                }
            }
        },
        "startdatum": {"type": "date", "format": "date"},
        "einddatum": {"type": "date", "format": "date"},
        "datum_goedkeuring": {"type": "date", "format": "date"},
        "beheerscommissie": {"type": "boolean"},
        "geometrie": {"type": "geo_shape"},
        "erfgoedobjecten": {"type": "keyword"},
        "plantype": {
            "type": "keyword",
            "fields": {"lower": {"type": "keyword", "normalizer": "keyword_lowercase"}},
        },
        "plantype_naam": {
            "type": "keyword",
            "fields": {"lower": {"type": "keyword", "normalizer": "keyword_lowercase"}},
        },
        "acls": {"type": "keyword", "normalizer": "keyword_lowercase"},
        "provincie": {
            "type": "keyword",
        },
        "gemeenten": {
            "properties": {
                "id": {"type": "long"},
                "naam": {
                    "type": "keyword",
                    "fields": {
                        "lower": {"type": "keyword", "normalizer": "keyword_lowercase"}
                    },
                },
                "niscode": {"type": "long"},
            }
        },
        "provincies": {
            "properties": {
                "naam": {
                    "type": "keyword",
                    "fields": {
                        "lower": {"type": "keyword", "normalizer": "keyword_lowercase"}
                    },
                },
                "niscode": {"type": "long"},
            }
        },
        "status": {
            "type": "object",
            "properties": {
                "datum": {"type": "date", "format": "date_optional_time"},
                "aanpasser_uri": {"type": "text"},
                "aanpasser_omschrijving": {"type": "text"},
                "status": {"type": "integer"},
                "actief": {"type": "boolean"},
            },
        },
    }
}


def map_es_beheersplannen_result(result, settings=None):
    settings = {} if settings is None else settings
    _uri = settings.get("plannen.uri", "https://id.erfgoed.net/plannen/{0}")
    _self = settings.get(
        "plannen.self",
        lambda r, id, **kwargs: "https://plannen.onroerenderfgoed.be/plannen/{0}".format(
            id
        ),
    )
    plannen = []
    for h in result["hits"]["hits"]:
        data = h["_source"]
        plannen.append(
            {
                "id": data["id"],
                "uri": _uri.format(data["id"]),
                "self": _self("beheersplan", id=(data["id"])),
                "onderwerp": data["onderwerp"] if "onderwerp" in data else "",
                "startdatum": data["startdatum"] if "startdatum" in data else "",
                "einddatum": data["einddatum"] if "einddatum" in data else "",
                "datum_goedkeuring": data["datum_goedkeuring"]
                if "datum_goedkeuring" in data
                else "",
                "beheerscommissie": data["beheerscommissie"]
                if "beheerscommissie" in data
                else "",
                "geometrie": data["geometrie"] if "geometrie" in data else "",
                "plantype": data["plantype"] if "plantype" in data else "",
                "plantype_naam": data["plantype_naam"] if "plantype_naam" in data else "",
                "bestanden": data["bestanden"] if "bestanden" in data else "",
                "erfgoedobjecten": data["erfgoedobjecten"]
                if "erfgoedobjecten" in data
                else "",
                "primair_bestand": data["primair_bestand"]
                if "primair_bestand" in data
                else None,
                "systemfields": data["systemfields"] if "systemfields" in data else None,
                "status": data["status"] if "status" in data else None,
                "actief": data["status"]["actief"] if "status" in data else None,
            }
        )
    return plannen
