import logging
import os

import backoff
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError

from services.exceptions import CONNECTION_EXCEPTIONS
from tests.functional.settings import test_settings

logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@backoff.on_exception(backoff.expo, CONNECTION_EXCEPTIONS)
def main():
    es_client = Elasticsearch(
        hosts=test_settings.elastic_host,
        validate_cert=False,
        use_ssl=False
    )
    if es_client.ping():
        logger.info("Elasticsearch connection OK")
        return
    else:
        logger.info("Waiting for connection to Elasticsearch...")
        raise ConnectionError


if __name__ == '__main__':
    main()
