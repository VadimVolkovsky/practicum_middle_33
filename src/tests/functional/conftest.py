import asyncio

import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch._async.helpers import async_bulk
from httpx import AsyncClient

from main import app
from tests.functional.settings import test_settings
from tests.functional.testdata import es_test_data


@pytest_asyncio.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(
        hosts=test_settings.elastic_host,
        verify_certs=False,
        use_ssl=False
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def get_es_bulk_query():
    async def inner(es_data, es_index):
        bulk_query: list[dict] = []

        for row in es_data:
            # Преобразуем модель pydantic в словарь
            row = row if isinstance(row, dict) else dict(row)

            data = {'_index': es_index, '_id': row['id']}
            data.update({'_source': row})
            bulk_query.append(data)

        return bulk_query
    return inner


@pytest_asyncio.fixture
async def es_write_data(es_client: AsyncElasticsearch, get_es_bulk_query):
    async def inner(es_index, data: list[dict], es_index_schema):
        if await es_client.indices.exists(index=es_index):
            await es_client.indices.delete(index=es_index)
        await es_client.indices.create(index=es_index, body=es_index_schema)

        bulk_query = await get_es_bulk_query(data, es_index)
        response, errors = await async_bulk(client=es_client, actions=bulk_query, refresh=True)

        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')

    return inner


@pytest_asyncio.fixture(scope='session')
async def async_client():
    async with AsyncClient(app=app, base_url=test_settings.service_url) as client:
        yield client


@pytest_asyncio.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# @pytest_asyncio.fixture(scope='session')
# async def api_session(event_loop):
#     session = aiohttp.ClientSession()
#     yield session
#     await session.close()
#
#
# @dataclass
# class HTTPResponse:
#     body: dict
#     headers: CIMultiDictProxy[str]
#     status: int
#
#
# @pytest_asyncio.fixture
# async def get_request(api_session):
#     async def inner(url, query):
#         async with api_session.get(url, params=query) as response:
#             return HTTPResponse(
#                 body=await response.json(),
#                 headers=response.headers,
#                 status=response.status,
#             )

@pytest_asyncio.fixture
async def get_es_data():
    async def inner():
        es_data = es_test_data.es_data
        return es_data
    return inner
