import pytest_asyncio
from elasticsearch._async.helpers import async_bulk

from elasticsearch import AsyncElasticsearch
from tests.functional.testdata import es_test_film_data, es_test_genres_data, es_test_persons_data


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


@pytest_asyncio.fixture
async def get_es_data():
    async def inner(es_index):
        match es_index:
            case 'movies':
                es_data = es_test_film_data.es_film_data
            case 'genres':
                es_data = es_test_genres_data.es_genres_data
            case 'persons':
                es_data = es_test_persons_data.es_persons_data
            case _:
                raise Exception(f'Не найдены тестовые данные для индекса {es_index}')
        return es_data
    return inner
