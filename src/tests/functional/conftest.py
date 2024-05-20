import pytest
from elasticsearch import AsyncElasticsearch
from elasticsearch._async.helpers import async_bulk
from httpx import AsyncClient

from main import app
from schemas.es_schemas import elastic_film_index_schema
from tests.functional.settings import test_settings


@pytest.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts=test_settings.es_host)
    yield client
    await client.close()


@pytest.fixture
async def get_es_bulk_query():
    async def inner(data):
        bulk_query: list[dict] = []

        for row in data:
            data = {'_index': 'movies', '_id': row['id']}
            data.update({'_source': row})
            bulk_query.append(data)

        # str_query = '\n'.join(bulk_query) + '\n'
        return bulk_query
    return inner


@pytest.fixture
async def es_write_data(es_client: AsyncElasticsearch, get_es_bulk_query):
    async def inner(data: list[dict]):
        if await es_client.indices.exists(index='movies'):
            await es_client.indices.delete(index='movies')
        await es_client.indices.create(index='movies', body=elastic_film_index_schema)

        bulk_query = await get_es_bulk_query(data)
        # response = await es_client.bulk(bulk_query, refresh=True)
        response , errors = await async_bulk(client=es_client, actions=bulk_query, refresh=True)

        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')

    return inner


@pytest.fixture(scope='session')
async def async_client():
    async with AsyncClient(app=app, base_url=test_settings.service_url) as client:
        yield client

# @pytest.fixture
# def make_get_request():
