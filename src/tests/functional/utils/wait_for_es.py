import time

from elasticsearch import Elasticsearch
# from core.config import app_settings


if __name__ == '__main__':
    es_client = Elasticsearch(
        hosts='elasticsearch:9200',  # TODO вынести в окружение
        validate_cert=False,
        use_ssl=False
    )
    while True:
        if es_client.ping():
            break
        time.sleep(1)
