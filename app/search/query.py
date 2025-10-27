from datetime import date
from datetime import datetime
from datetime import timedelta

from oe_utils.search import parse_sort_string as oe_parse_sort_string
from oe_utils.search.query_builder import QueryBuilder


def date_format_converter(date_text):
    return datetime.strptime(date_text, "%d-%m-%Y").strftime("%Y-%m-%d")


class PlannenQueryBuilder(QueryBuilder):
    def __init__(self):
        super().__init__()
        self.queryparam_to_es_fields.update(
            {
                "provincie": ["provincies.naam.lower", "provincies.niscode"],
                "gemeente": ["gemeenten.naam.lower", "gemeenten.niscode"],
                "id": ["id"],
                "erfgoedobjecten": ["erfgoedobjecten"],
                "aanduidingsobject": ["erfgoedobjecten"],
                "plantype": ["plantype.lower", "plantype_naam.lower"],
                "type": ["plantype", "plantype_naam"],
                "status": ["status.status"],
                "beheerscommissie": ["beheerscommissie"],
                "aanduidingsobjecttype": [
                    "aanduidingsobjecttypes.naam.keyword",
                    "aanduidingsobjecttypes.uri.keyword",
                ]
            }
        )
        self.queryparam_to_filter_method.update(
            {
                "onderwerp": (self._build_onderwerp_filter,),
                "jaar_goedkeuring": (self._add_date_filter,),
                "datum_goedkeuring_van": (self._build_goedkeuring_van_filter,),
                "datum_goedkeuring_tot": (self._build_goedkeuring_tot_filter,),
                "beheersplan_verlopen": (self._build_beheersplan_verlopen_filter,),
            }
        )
        self.text_boosted_fields = [{"*": 1}]

    def add_user_filter(self, user_acls):
        self.filters.append({"terms": {"acls": user_acls}})

    def _build_goedkeuring_van_filter(self, filter_value):
        return {
            "range": {"datum_goedkeuring": {"gte": filter_value.strftime("%Y-%m-%d")}}
        }

    def _build_goedkeuring_tot_filter(self, filter_value):
        return {
            "range": {"datum_goedkeuring": {"lte": filter_value.strftime("%Y-%m-%d")}}
        }

    def _build_beheersplan_verlopen_filter(self, filter_value):
        # verlopen = einddatum < vandaag = datum_goedkeuring <= gisteren
        if filter_value:
            return {
                "range": {
                    "einddatum": {
                        "lte": (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
                    }
                }
            }
        return {
            "range": {"einddatum": {"gte": (date.today()).strftime("%Y-%m-%d")}}
        }

    def _build_onderwerp_filter(self, value):
        return {
            "simple_query_string": {
                "fields": ["onderwerp"],
                "query": value,
                "default_operator": "AND",
                "flags": "AND|OR|NOT|PREFIX|PHRASE|PRECEDENCE|ESCAPE|WHITESPACE",
                "analyze_wildcard": True,
            }
        }

    def _add_date_filter(self, value):
        return {
            "range": {
                "datum_goedkeuring": {
                    "gte": date(int(value), 1, 1).isoformat(),
                    "lte": date(int(value), 12, 31).isoformat(),
                }
            }
        }

    # def set_full_text_search_query(self, *args, **kwargs):
    #     super().set_full_text_search_query(*args, **kwargs)
    #     self.query["simple_query_string"]["lenient"] = True

    def prepare_filters(self):
        self.add_user_filter(self.user_acls)
        super().prepare_filters()


class ResourceQueryBuilder(QueryBuilder):
    def add_date_filter(self):
        if "jaar_goedkeuring" not in self.query_params:
            return
        jaren = self.query_params["jaar_goedkeuring"]
        if not isinstance(jaren, list):
            jaren = [jaren]
        filters = []
        for of in jaren:
            filters.append(
                {
                    "range": {
                        "datum_goedkeuring": {
                            "gte": date(int(of), 1, 1).isoformat(),
                            "lte": date(int(of), 12, 31).isoformat(),
                        }
                    }
                }
            )
        self.filters.append(filters[0] if len(filters) == 1 else self.or_(*filters))

    def add_user_filter(self, user_acls):
        self.filters.append({"terms": {"acls": user_acls}})

    def _build_concept_term(self, concept_name, concept, lower=False):
        filter_method = "match"
        value = str(concept).lower() if lower else str(concept)
        return {filter_method: {concept_name: value}}


def parse_sort_string(sort):
    return oe_parse_sort_string(
        sort,
        status="status.status",
        onderwerp="onderwerp.raw",
        datumgoedkeuring="datum_goedkeuring",
        actief="status.actief",
    )
