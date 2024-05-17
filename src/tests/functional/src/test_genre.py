import aiohttp
import pytest
from faker import Faker

from es_data_generation import GenreSchema
from tests.functional.settings import test_settings
from schemas.es_schemas import elastic_genre_index_schema

fake = Faker()


@pytest.mark.asyncio
async def test_genre_add(es_client, es_write_data):
    es_index = 'genres'
    genres = ['Action', 'Western', 'Detective', 'Drama', 'Comedy', 'Melodrama', ]
    data = [GenreSchema(id=fake.uuid4(), name=name) for name in genres]

    # создаем индекс
    if await es_client.indices.exists(index=es_index):
        await es_client.indices.delete(index=es_index)
    await es_client.indices.create(index=es_index, body=elastic_genre_index_schema)

    # загружаем данные в эластик
    await es_write_data(es_index, data)

    # получаем загруженные данные из эластика
    session = aiohttp.ClientSession()
    genre_id = data[0].id
    genre_name = data[0].name
    url = test_settings.service_url + f'/api/v1/genres/{genre_id}'
    query_data = {'genre_id': genre_id}

    async with session.get(url, params=query_data) as response:
        body = await response.json()
        status = response.status
    await session.close()

    # проверяем
    assert status == 200
    assert body['id'] == genre_id
    assert body['name'] == genre_name
