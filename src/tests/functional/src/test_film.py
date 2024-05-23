from http import HTTPStatus

import pytest

from db.elastic import Indexes
from schemas.es_schemas import elastic_film_index_schema
from tests.functional.settings import test_settings


@pytest.mark.parametrize(
    'film_id, expected_answer',
    [
        ('64afe9bc-6ea9-4843-8c5a-a76007614b45', {'status': HTTPStatus.OK, 'count_recommended': 3}),
        ('0000000', {'status': HTTPStatus.NOT_FOUND}),
    ]
)
@pytest.mark.asyncio
async def test_get_film_detail(get_es_data, es_write_data, film_id, expected_answer, get_request) -> None:
    es_index = Indexes.movies.value.get('index_name')
    es_film_data = await get_es_data(es_index)
    await es_write_data(es_index=es_index, data=es_film_data, es_index_schema=elastic_film_index_schema)

    url = test_settings.service_url + f'/api/v1/films/{film_id}'

    response = await get_request(url)
    status = response.status
    body = response.body

    assert status == expected_answer['status']

    if status == HTTPStatus.OK:
        assert 'recommended_films' in body
        assert len(body['recommended_films']) == expected_answer['count_recommended']
        assert body['recommended_films'][0]['imdb_rating'] >= body['recommended_films'][1]['imdb_rating']


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'page_number': 1, 'page_size': 5, 'sort': '-imdb_rating'}, {'status': HTTPStatus.OK, 'count': 5,
                                                                      'rating_higher': True}),
        ({'page_number': 2, 'page_size': 5}, {'status': HTTPStatus.OK, 'count': 5}),
        ({'page_number': 1}, {'status': HTTPStatus.OK, 'count': 10}),
        ({'page_number': 1, 'sort': 'imdb_rating'}, {'status': HTTPStatus.OK, 'count': 10, 'rating_higher': False}),
        ({'sort': '-imdb_rating', 'genre': 'cfaec163-d52b-4cc9-a791-35ccfdb7f7e0'}, {'status': HTTPStatus.OK, 'count': 5,
                                                                                     'rating_higher': True}),
        ({'page_number': '-1'}, {'status': HTTPStatus.UNPROCESSABLE_ENTITY}),
        ({'genre': 'Unknown'}, {'status': HTTPStatus.NOT_FOUND}),
    ]
)
@pytest.mark.asyncio
async def test_get_film_list(get_es_data, es_write_data, expected_answer, query_data, get_request):
    es_index = Indexes.movies.value.get('index_name')
    es_film_data = await get_es_data(es_index)
    await es_write_data(es_index=es_index, data=es_film_data, es_index_schema=elastic_film_index_schema)

    url = test_settings.service_url + '/api/v1/films'
    query_params = query_data

    response = await get_request(url, params=query_params)
    status = response.status
    body = response.body

    assert status == expected_answer['status']

    if status == HTTPStatus.OK:
        assert len(body) == expected_answer['count']

    if query_data.get('sort', None):
        assert bool(
            body[0]['imdb_rating'] >= body[1]['imdb_rating']
        ) is expected_answer['rating_higher']
