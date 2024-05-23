from http import HTTPStatus

import pytest
from faker import Faker

from db.elastic import Indexes
from schemas.es_schemas import elastic_person_index_schema, elastic_film_index_schema
from tests.functional.settings import test_settings

fake = Faker()

roles = {
    'directors': 'director',
    'actors': 'actor',
    'writers': 'writer'
}


@pytest.mark.parametrize(
    'person, expected_answer',
    [
        ({'id': '79dcd2f3-97d0-46df-bdff-63c36775288f', 'name': 'Daniel Holden'}, {'status': HTTPStatus.OK}),
        ({'id': '0000000', 'name': 'fake_person'}, {'status': HTTPStatus.NOT_FOUND}),
    ]
)
@pytest.mark.asyncio
async def test_person_get_by_id_without_films(get_es_data, es_write_data, person, expected_answer, get_request):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/{person_id}
     возвращает персонажа с пустым списком фильмов
    """

    es_index = Indexes.persons.value.get('index_name')
    es_persons_data = await get_es_data(es_index)
    await es_write_data(es_index, es_persons_data, elastic_person_index_schema)
    url = test_settings.service_url + f"/api/v1/persons/{person['id']}"

    response = await get_request(url)
    status = response.status
    body = response.body

    assert status == expected_answer['status']
    if status == HTTPStatus.OK:
        assert body['id'] == person['id']
        assert body['full_name'] == person['name']
        assert len(body['films']) == 0


@pytest.mark.parametrize(
    'person, expected_answer',
    [
        ({'id': '5bd7f73e-6648-4a4c-926a-13ec037c3fdf', 'name': 'David Martin'}, {'status': HTTPStatus.OK}),
    ]
)
@pytest.mark.asyncio
async def test_person_get_by_id_with_films(get_es_data, es_write_data, person, expected_answer, get_request):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/{person_id}
     возвращает персонажа с перечислением его списка фильмов.
    """

    es_person_index = Indexes.persons.value.get('index_name')
    es_movies_index = Indexes.movies.value.get('index_name')
    es_persons_data = await get_es_data(es_person_index)
    es_movies_data = await get_es_data(es_movies_index)
    await es_write_data(es_person_index, es_persons_data, elastic_person_index_schema)
    await es_write_data(es_movies_index, es_movies_data, elastic_film_index_schema)

    url = test_settings.service_url + f"/api/v1/persons/{person['id']}"
    response = await get_request(url)
    status = response.status
    body = response.body

    assert status == expected_answer['status']
    if status == HTTPStatus.OK:
        assert body['id'] == person['id']
        assert body['full_name'] == person['name']
        assert len(body['films']) == 2


@pytest.mark.parametrize(
    'person_films, expected_answer',
    [
        ([
             {'id': '64afe9bc-6ea9-4843-8c5a-a76007614b45', 'title': 'Deploy Strategic Mindshare', 'imdb_rating': 4},
             {'id': '598baf06-d300-4567-8ab5-1b11079691cf', 'title': 'Implement Value-Added Users', 'imdb_rating': 7.8}
         ], {'status': HTTPStatus.OK}),
    ]
)
@pytest.mark.asyncio
async def test_get_person_films_by_id(get_es_data, es_write_data, person_films, expected_answer, get_request):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/{person_id}/film
     возвращает список фильмов персонажа
    """

    es_person_index = Indexes.persons.value.get('index_name')
    es_movies_index = Indexes.movies.value.get('index_name')
    es_persons_data = await get_es_data(es_person_index)
    es_movies_data = await get_es_data(es_movies_index)
    await es_write_data(es_person_index, es_persons_data, elastic_person_index_schema)
    await es_write_data(es_movies_index, es_movies_data, elastic_film_index_schema)

    person_id = '5bd7f73e-6648-4a4c-926a-13ec037c3fdf'
    url = test_settings.service_url + f'/api/v1/persons/{person_id}/film'
    response = await get_request(url)
    status = response.status
    body = response.body

    assert status == HTTPStatus.OK
    assert len(body) == 2
    for i in range(len(person_films)):
        assert body[i]['id'] == person_films[i]['id']
        assert body[i]['title'] == person_films[i]['title']
        assert body[i]['imdb_rating'] == person_films[i]['imdb_rating']


@pytest.mark.parametrize(
    'person, expected_answer',
    [
        (
                {
                    'id': '5bd7f73e-6648-4a4c-926a-13ec037c3fdf',
                    'full_name': 'David Martin',
                    'films': [
                        {'id': '64afe9bc-6ea9-4843-8c5a-a76007614b45', 'roles': 'director'},
                        {'id': '598baf06-d300-4567-8ab5-1b11079691cf', 'roles': 'director'},
                    ],
                },
                {'status': HTTPStatus.OK}),
    ]
)
@pytest.mark.asyncio
async def test_search_person(get_es_data, es_write_data, person, expected_answer, get_request):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/search
    находит персонажа по имени и возвращает список его фильмов
    """

    es_person_index = Indexes.persons.value.get('index_name')
    es_movies_index = Indexes.movies.value.get('index_name')
    es_persons_data = await get_es_data(es_person_index)
    es_movies_data = await get_es_data(es_movies_index)
    await es_write_data(es_person_index, es_persons_data, elastic_person_index_schema)
    await es_write_data(es_movies_index, es_movies_data, elastic_film_index_schema)

    url = test_settings.service_url + '/api/v1/persons/search'
    query_data = {'query': person['full_name']}
    response = await get_request(url, params=query_data)
    status = response.status
    body = response.body

    assert status == HTTPStatus.OK
    assert body[0]['id'] == person['id']
    assert body[0]['full_name'] == person['full_name']
    assert len(body[0]['films']) == 2
    for i in range(len(person['films'])):
        assert body[0]['films'][i]['id'] == person['films'][i]['id']
        assert body[0]['films'][i]['id'] == person['films'][i]['id']
