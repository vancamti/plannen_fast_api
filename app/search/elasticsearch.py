from elasticsearch import Elasticsearch

from app.core.config import settings


class ElasticsearchClient:
    """Elasticsearch client wrapper."""

    def __init__(self):
        self.client = None

    def connect(self):
        """Initialize Elasticsearch connection."""
        if not self.client:
            self.client = Elasticsearch([settings.ELASTICSEARCH_URL])
        return self.client

    def close(self):
        """Close Elasticsearch connection."""
        if self.client:
            self.client.close()
            self.client = None

    def get_index_name(self, base_name: str) -> str:
        """Get full index name with prefix."""
        return f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{base_name}"


es_client = ElasticsearchClient()


def get_es():
    """Dependency to get Elasticsearch client."""
    return es_client.connect()
