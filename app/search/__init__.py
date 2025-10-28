import logging

from oe_utils.search.searchengine import ISearchEngine
from oe_utils.search.searchengine import SearchEngine

log = logging.getLogger(__name__)

beheersplan_aggregations = {
    "plantypes": {"terms": {"field": "plantype", "order": {"_key": "asc"}, "size": 8}},
    "provincies": {
        "terms": {"field": "provincies.naam", "order": {"_key": "asc"}, "size": 5}
    },
    "gemeente": {
        "terms": {"field": "gemeenten.naam", "order": {"_key": "asc"}, "size": 581}
    },
    "jaar_goedkeuring": {
        "date_histogram": {
            "field": "datum_goedkeuring",
            "order": {"_key": "asc"},
            "calendar_interval": "year",
            "min_doc_count": 1,
            "format": "yyyy",
        }
    },
    "aanduidingsobjecttypes": {
        "terms": {
            "field": "aanduidingsobjecttypes.naam.keyword",
            "order": {"_key": "asc"},
            "size": 30,
        }
    },
}


class SearchHelper:
    """
    Object om te helpen bij het presenteren van zoekresultaten.
    """

    aggregation_filter_map = {
        "plantypes": "plantype",
        "provincies": "provincie",
        "gemeente": "gemeente",
        "jaar_goedkeuring": "jaar_goedkeuring",
        "aanduidingsobjecttypes": "aanduidingsobjecttype",
    }

    aggregation_label_map = {
        "jaar_goedkeuring": "Jaar goedkeuring",
        "aanduidingsobjecttypes": "Type aanduidingsobject",
    }

    aggregation_provider_map = {
        "plantypes": "PLANTYPES",
    }

    aggregation_coding_map = {}

    aggregation_order = [
        "plantypes",
        "provincies",
        "gemeente",
        "jaar_goedkeuring",
        "aanduidingsobjecttypes",
    ]
    sort_order_map = {
        "onderwerp": "onderwerp",
        "id": "id",
        "datum_goedkeuring": "datum goedkeuring",
    }

    status_map = {10: "klad", 25: "klaar voor activatie", 75: "actief"}

    expandable_aggregations = [
        "provincies",
        "gemeente",
        "jaar_goedkeuring",
        "aanduidingsobjecttypes",
    ]

    def __init__(self, request):
        self.request = request

    def get_filter_for_aggregation(self, aggregationname):
        """
        Zoek de naam van de filter op die bij een bepaalde aggregation hoort.
        """
        return self.aggregation_filter_map.get(aggregationname, None)

    def get_provider_for_aggregation(self, aggregationname):
        """
        Zoek de naam van de provider op die bij een bepaalde aggregation hoort.
        """
        return self.aggregation_provider_map.get(aggregationname, None)


def get_search_helper(request):
    return SearchHelper(request)


def fix_aggregations(aggregations):
    for key in aggregations.keys():
        if beheersplan_aggregations.get(key, {}).get("terms", {}).get("order"):
            continue
        entries = aggregations[key].get("buckets", [])
        aggregations[key]["buckets"] = sorted(entries, key=lambda k: k["doc_count"])
        aggregations[key]["buckets"].reverse()
    for year in aggregations["jaar_goedkeuring"]["buckets"]:
        year["key"] = year["key_as_string"]
    return aggregations

