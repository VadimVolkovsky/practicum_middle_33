import aiohttp
import pytest

from db.elastic import Indexes
from schemas.es_schemas import elastic_film_index_schema
from tests.functional.settings import test_settings


@pytest.mark.parametrize(
    'film_id, expected_answer',
    [
        ('3ee69719-dca0-4bc0-8cba-ad0d77fdf52d', {'status': 200, 'count_recommended': 3}),
        ('0000000', {'status': 404}),
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

    if status == 200:
        assert 'recommended_films' in body
        assert len(body['recommended_films']) == expected_answer['count_recommended']
        assert body['recommended_films'][0]['imdb_rating'] >= body['recommended_films'][1]['imdb_rating']


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'page_number': 1, 'page_size': 5, 'sort': '-imdb_rating'}, {'status': 200, 'count': 5,
                                                                      'rating_higher': True}),
        ({'page_number': 2, 'page_size': 5}, {'status': 200, 'count': 5}),
        ({'page_number': 1}, {'status': 200, 'count': 10}),
        ({'page_number': 1, 'sort': 'imdb_rating'}, {'status': 200, 'count': 10, 'rating_higher': False}),
        ({'sort': '-imdb_rating', 'genre': '6f476c58-40e3-48a1-a10f-0f23e368fb66'}, {'status': 200, 'count': 8,
                                                                                     'rating_higher': True}),
        ({'page_number': '-1'}, {'status': 422}),
        ({'genre': 'Unknown'}, {'status': 404}),
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

    if status == 200:
        assert len(body) == expected_answer['count']

    if query_data.get('sort', None):
        assert bool(
            body[0]['imdb_rating'] >= body[1]['imdb_rating']
        ) is expected_answer['rating_higher']
