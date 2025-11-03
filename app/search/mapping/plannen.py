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
                "id": {"type": "long"},
                "naam": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "keyword_lowercase",
                        }
                    },
                },
                "uri": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
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


def map_es_beheersplannen_result(self_url, result, settings):
    _uri = settings.PLANNEN_URI
    plannen = []
    for h in result["hits"]["hits"]:
        data = h["_source"]
        plannen.append(
            {
                "id": data["id"],
                "uri": _uri.format(id=data["id"]),
                "self": str(self_url).format(id=data["id"]),
                "onderwerp": data.get("onderwerp", ""),
                "startdatum": data.get("startdatum", ""),
                "einddatum": data.get("einddatum", ""),
                "datum_goedkeuring": data.get("datum_goedkeuring", ""),
                "beheerscommissie": data.get("beheerscommissie", ""),
                "geometrie": data.get("geometrie", ""),
                "plantype": data.get("plantype", ""),
                "plantype_naam": data.get("plantype_naam", ""),
                "bestanden": data.get("bestanden", ""),
                "erfgoedobjecten": data.get("erfgoedobjecten", ""),
                "primair_bestand": data.get("primair_bestand"),
                "systemfields": data.get("systemfields"),
                "status": data.get("status"),
                "actief": data.get("status", {}).get("actief"),
            }
        )
    return plannen
