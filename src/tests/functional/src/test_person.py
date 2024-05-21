import random

import aiohttp
import pytest
from faker import Faker

from es_data_generation import PersonSchema, FilmWorkSchema, GenreSchema
from tests.functional.settings import test_settings
from schemas.es_schemas import elastic_person_index_schema, elastic_film_index_schema

fake = Faker()

es_persons_index = 'persons'
es_films_index = 'movies'
roles = {
    'directors': 'director',
    'actors': 'actor',
    'writers': 'writer'
}
genres = ['Action', 'Western', 'Detective', 'Drama', 'Comedy', 'Melodrama', ]
genres_data = [GenreSchema(id=fake.uuid4(), name=name) for name in genres]
persons_data = [
    PersonSchema(
        id=fake.uuid4(),
        name=fake.name(),
        role=random.choice(list(roles.values())))
    for _ in range(5)
]

films_data = [FilmWorkSchema(
    id=fake.uuid4(),
    imdb_rating=round(random.uniform(1, 10), 1),
    genre=random.sample(genres_data, k=random.randint(1, 3)),
    title=fake.bs().title(),
    persons=persons_data,
    description=fake.text(),
) for _ in range(5)]


@pytest.mark.asyncio
async def test_person_get_by_id_without_films(es_client, es_write_data):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/{person_id}
     возвращает персонажа с пустым списком фильмов
    """

    # загружаем данные в эластик
    await es_write_data(es_persons_index, persons_data, elastic_person_index_schema)

    session = aiohttp.ClientSession()
    person_id = persons_data[0].id
    person_name = persons_data[0].name
    url = test_settings.service_url + f'/api/v1/persons/{person_id}'
    query_data = {'person_id': person_id}

    async with session.get(url, params=query_data) as response:
        body = await response.json()
        status = response.status
    await session.close()

    # проверяем
    assert status == 200
    assert body['id'] == person_id
    assert body['full_name'] == person_name
    assert body['films'] == []


@pytest.mark.asyncio
async def test_person_get_by_id_with_films(es_client, es_write_data):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/{person_id}
     возвращает персонажа с перечислением его списка фильмов.
    """

    # загружаем данные в эластик
    await es_write_data(es_persons_index, persons_data, elastic_person_index_schema)
    await es_write_data(es_films_index, films_data, elastic_film_index_schema)

    session = aiohttp.ClientSession()
    person_id = persons_data[0].id
    person_name = persons_data[0].name
    person_role = persons_data[0].role
    url = test_settings.service_url + f'/api/v1/persons/{person_id}'
    query_data = {'person_id': person_id}

    async with session.get(url, params=query_data) as response:
        body = await response.json()
        status = response.status
    await session.close()

    # проверяем
    assert status == 200
    assert body['id'] == person_id
    assert body['full_name'] == person_name
    assert len(body['films']) == 5
    assert body['films'][0]['id'] == films_data[0].id
    assert body['films'][0]['roles'] == [person_role]


@pytest.mark.asyncio
async def test_get_person_films_by_id(es_client, es_write_data):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/{person_id}/film
     возвращает список фильмов персонажа
    """

    # загружаем данные в эластик
    await es_write_data(es_persons_index, persons_data, elastic_person_index_schema)
    await es_write_data(es_films_index, films_data, elastic_film_index_schema)

    session = aiohttp.ClientSession()
    person_id = persons_data[0].id
    url = test_settings.service_url + f'/api/v1/persons/{person_id}/film'
    query_data = {'person_id': person_id}

    async with session.get(url, params=query_data) as response:
        body = await response.json()
        status = response.status
    await session.close()

    # проверяем
    assert status == 200
    assert len(body) == 5
    assert body[0]['id'] == films_data[0].id
    assert body[0]['title'] == films_data[0].title
    assert body[0]['imdb_rating'] == films_data[0].imdb_rating


@pytest.mark.asyncio
async def test_search_person(es_client, es_write_data):
    """
    Тест проверяет, что эндпоинт /api/v1/persons/search
    находит персонажа по имени и возвращает список его фильмов
    """

    # загружаем данные в эластик
    await es_write_data(es_persons_index, persons_data, elastic_person_index_schema)
    await es_write_data(es_films_index, films_data, elastic_film_index_schema)

    session = aiohttp.ClientSession()
    person_id = persons_data[0].id
    person_name = persons_data[0].name
    person_role = persons_data[0].role
    url = test_settings.service_url + '/api/v1/persons/search'
    query_data = {'query': person_name}

    async with session.get(url, params=query_data) as response:
        body = await response.json()
        status = response.status
    await session.close()

    # проверяем
    assert status == 200
    assert body[0]['id'] == person_id
    assert body[0]['full_name'] == person_name
    assert len(body[0]['films']) == 5
    assert body[0]['films'][0]['id'] == films_data[0].id
    assert body[0]['films'][0]['roles'] == [person_role]

# TODO вынести генерацию тестовых данных в аналог SetUp
