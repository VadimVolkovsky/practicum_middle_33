import logging
import os
import random
from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from constants import ListDictType, OptStrType
from db.elastic import Indexes
from services.film import FilmService, get_film_service
from services.utils import validation_index_model_field


router = APIRouter()
logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.INFO)


class FilmListSerializer(BaseModel):
    '''модель для возврата списка фильмов из API'''

    id: str
    title: str
    imdb_rating: float


class FilmSerializer(FilmListSerializer):
    '''модель для возврата экземпляра фильма из API'''

    description: str
    genre: ListDictType
    directors: ListDictType
    actors: ListDictType
    writers: ListDictType
    file_path: OptStrType = None
    creation_date: datetime | None = None
    recommended_films: list[FilmListSerializer]


@router.get('/search',
            response_model=list[FilmListSerializer],
            description="""Выполните запрос на поиск фильмов по названию, где:
    query - строка, по которой производится полнотекстовый поиск
    page_number - номер страницы
    page_size - размер станицы
    sort - поле, по которому ссортируется список
    В ответе будет выведен список фильмов с id, названием и рейтингом.
    """)
async def film_search(query: str,
                      page_number: int = Query(1, gt=0),
                      page_size: int = Query(100, gt=0),
                      sort: OptStrType = None,
                      film_service: FilmService = Depends(get_film_service)) -> list[FilmListSerializer]:
    '''Метод для поиска подходящих по названию фильмов
    :param query: строка, по которой производится полнотекстовый поиск
    :param page_number: номер страницы
    :param page_size: размер станицы
    :param sort: поле, по которому ссортируется список'''

    start_index = (page_number - 1) * page_size
    index_model = Indexes.movies.value.get('index_model')
    sort = await validation_index_model_field(sort, index_model)

    film_list = await film_service.get_list_film(start_index, page_size, sort=sort, query=query)

    if not film_list:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [FilmListSerializer(**dict(film)) for film in film_list]


@router.get('/{film_id}',
            response_model=FilmSerializer,
            description="""Выполните запрос на поиск фильма по его id,
            в ответе будет выведен подробная информация о фильме""")
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> FilmSerializer:
    """
    Метод возвращает сериализованный объект фильма по id.
    В случае отсутствия фильма с указанным id - возвращает код ответа 404
    :param film_id: id экземпляра фильма
    """
    try:
        index_dict = Indexes.movies.value
        film = await film_service.get_by_id(film_id, index_dict)

        if not film:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

        # TODO add several genres

        # genres = [genre['id'] for genre in film.genre]
        genres = random.choice([genre['id'] for genre in film.genre])
        recommended_film_list = await film_service.get_list_film(start_index=0, page_size=3, sort='-imdb_rating',
                                                                 genre=genres)
        return FilmSerializer(
            recommended_films=[FilmListSerializer(**dict(film)) for film in recommended_film_list],
            **dict(film)
        )
    except KeyError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='index not found')


@router.get('', response_model=list[FilmListSerializer],
            description="""Выполните запрос на поиск фильмов, где:
                query - строка, по которой производится полнотекстовый поиск
                page_number: номер страницы
                page_size: размер станицы
                sort: поле, по которому ссортируется список
                genre: жанр, по которому фильтруется список фильмов
                В ответе будет выведен сериализованный список фильмов, с опциональной фильтрацией по жанру.
                В случае отсутствия подходяших фильмов - возвращает код ответа 404
                """
            )
async def film_list(page_number: int = Query(1, gt=0),
                    page_size: int = Query(100, gt=0),
                    sort: OptStrType = None,
                    genre: OptStrType = None,
                    film_service: FilmService = Depends(get_film_service)) -> list[FilmListSerializer]:
    """
    Метод возвращает сериализованный список фильмов, с опциональной фильтрацией по жанру.
    В случае отсутствия подходяших фильмов - возвращает код ответа 404
    :param page_number: номер страницы
    :param page_size: размер станицы
    :param sort: поле, по которому ссортируется список
    :param genre: жанр, по которому фильтруется список фильмов'''
    """
    index_model = Indexes.movies.value.get('index_model')
    sort = await validation_index_model_field(sort, index_model)
    start_index = (page_number - 1) * page_size

    film_list = await film_service.get_list_film(start_index, page_size, sort, genre)

    if not film_list:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [FilmListSerializer(**dict(film)) for film in film_list]
