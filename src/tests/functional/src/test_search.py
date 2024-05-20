import datetime
import uuid

import aiohttp
import pytest

from tests.functional.conftest import es_write_data
from tests.functional.settings import test_settings



@pytest.mark.asyncio
async def test_search(es_write_data, async_client):
    # 1. Генерируем данные для ES
    es_data = [{
        'id': str(uuid.uuid4()),
        'imdb_rating': 8.5,
        'genre': [
            {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f75', 'name':'Action'},
            {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f45', 'name': 'Sci-Fi'}
        ],
        'title': 'The Star',
        'description': 'New World',
        'actors': [
            {'id': 'ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95', 'name': 'Ann'},
            {'id': 'fb111f22-121e-44a7-b78f-b19191810fbf', 'name': 'Bob'}
        ],
        'writers': [
            {'id': 'caf76c67-c0fe-477e-8766-3ab3ff2574b5', 'name': 'Ben'},
            {'id': 'b45bd7bc-2e16-46d5-b125-983d356768c6', 'name': 'Howard'}
        ],

    } for _ in range(1)]

    # 2. Загружаем данные в ES

    # if await es_client.indices.exists(index=test_settings.es_index):
    #     await es_client.indices.delete(index=test_settings.es_index)

    # await es_client.indices.create(index=test_settings.es_index, **test_settings.es_index_mapping)

    await es_write_data(es_data)
    # updated, errors = await async_bulk(client=es_client, actions=bulk_query)


    # if errors:
    #     raise Exception('Ошибка записи данных в Elasticsearch')

    # 3. Запрашиваем данные из ES по API

    session = aiohttp.ClientSession()
    url = test_settings.service_url + '/api/v1/films'
    # query_data = {'search': 'ef86b8ff-3c82-4d31-ad8e-'}
    async with session.get(url) as response:
        body = await response.json()
        headers = response.headers
        status = response.status
    await session.close()

    # response = await async_client.get('/api/v1/films')
    # 4. Проверяем ответ

    assert response == 200
    # assert len(body) == 50