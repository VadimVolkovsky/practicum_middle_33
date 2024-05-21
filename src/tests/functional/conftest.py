from time import sleep

import pytest
from elasticsearch import AsyncElasticsearch, helpers

from tests.functional.settings import test_settings


# @pytest.fixture(scope='session')  # TODO  не выпоняются все тесты сразу т.к. закрывается евент луп после первого теста
@pytest.fixture
async def es_client():
    """Фикстура для подключения к эластику"""
    client = AsyncElasticsearch(
        hosts=test_settings.es_host,
        validate_cert=False,
        use_ssl=False
    )
    yield client
    await client.close()


@pytest.fixture
async def es_write_data(es_client: AsyncElasticsearch):
    """Фикстура для загрузки данных в эластик"""
    async def inner(es_index, data: list[dict]):
        await _load_data_to_elastic(es_client, es_index, data)
    return inner


async def _load_data_to_elastic(es_client, es_index, data):
    """Загрузка данных в эластик"""
    bulk_data = []

    for item in data:
        bulk_data.append({
            '_op_type': 'index',
            '_index': es_index,
            '_id': item.id,
            '_source': item.dict()
        })

    updated, errors = await helpers.async_bulk(es_client, bulk_data)
    if errors:
        raise Exception('Ошибка записи данных в Elasticsearch')
    sleep(2)  # для полной загрузки данных в эластик
    return updated


@pytest.fixture
async def es_create_index(es_client: AsyncElasticsearch):
    """Фикстура для создания нового индекса в эластике"""
    async def inner(es_index, es_index_schema):
        if await es_client.indices.exists(index=es_index):
            await es_client.indices.delete(index=es_index)
        await es_client.indices.create(index=es_index, body=es_index_schema)
    sleep(2)  # для полного создания индекса в эластике
    return inner
