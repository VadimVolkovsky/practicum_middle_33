from http import HTTPStatus

import pytest
from faker import Faker

from db.elastic import Indexes
from schemas.es_schemas import elastic_genre_index_schema
from tests.functional.settings import test_settings

fake = Faker()


@pytest.mark.parametrize(
    'genre, expected_answer',
    [
        ({'id': 'cfaec163-d52b-4cc9-a791-35ccfdb7f7e0', 'name': 'Western'}, {'status': HTTPStatus.OK}),
        ({'id': '0000000', 'name': 'fake_genre'}, {'status': HTTPStatus.NOT_FOUND}),
    ]
)
@pytest.mark.asyncio
async def test_get_genre_by_id(get_es_data, es_write_data, genre, expected_answer, get_request):
    es_index = Indexes.genres.value.get('index_name')
    es_genres_data = await get_es_data(es_index)
    await es_write_data(es_index, es_genres_data, elastic_genre_index_schema)
    url = test_settings.service_url + f"/api/v1/genres/{genre['id']}"

    response = await get_request(url)
    status = response.status
    body = response.body

    assert status == expected_answer['status']

    if status == HTTPStatus.OK:
        assert body['id'] == genre['id']
        assert body['name'] == genre['name']
