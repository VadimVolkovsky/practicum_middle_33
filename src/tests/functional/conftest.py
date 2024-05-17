import pytest
from elasticsearch import AsyncElasticsearch, helpers

from tests.functional.settings import test_settings


@pytest.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(
        hosts=test_settings.es_host,
        validate_cert=False,
        use_ssl=False
    )
    yield client
    await client.close()


@pytest.fixture
async def es_write_data(es_client: AsyncElasticsearch):
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
    return updated
