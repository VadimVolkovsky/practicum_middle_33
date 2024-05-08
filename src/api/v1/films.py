from datetime import datetime
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.film import FilmService, get_film_service
from services.utils import validation_index_model_fiield

router = APIRouter()


class FilmListSerializer(BaseModel):
    '''модель для возврата списка фильмов из API'''

    id: str
    title: str
    imdb_rating: float


class FilmSerializer(FilmListSerializer):
    '''модель для возврата экземпляра фильма из API'''

    description: str
    genre: list[dict[str, str]]
    directors: list[dict[str, str]]
    actors: list[dict[str, str]]
    writers: list[dict[str, str]]
    file_path: Optional[str]
    creation_date: Optional[datetime]


@router.get('/search', response_model=list[FilmListSerializer])
async def film_search(query: str,
                      page_number: int = Query(1, gt=0),
                      page_size: int = Query(100, gt=0),
                      sort: Optional[str] = None,
                      film_service: FilmService = Depends(get_film_service)) -> list[FilmListSerializer]:
    '''Эндпоинт для полнотекстового поиска
    :param query: строка, по которой производится полнотекстовый поиск
    :param page_number: номер страницы
    :param page_size: размер станицы
    :param sort: поле, по которому ссортируется список'''

    start_index = (page_number - 1) * page_size
    sort = await validation_index_model_fiield(sort)

    film_list = await film_service.get_list_film(start_index, page_size, sort=sort, query=query)

    if not film_list:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [FilmListSerializer(**dict(film)) for film in film_list]


@router.get('/{film_id}', response_model=FilmSerializer)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> FilmSerializer:
    """
    Метод возвращает сериализованный объект фильма по id.
    В случае отсутствия фильма с указанным id - возвращает код ответа 404
    :param film_id: id экземпляра фильма
    """

    film = await film_service.get_by_id(film_id)

    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return FilmSerializer(**dict(film))


@router.get('', response_model=list[FilmListSerializer])
async def film_list(page_number: int = Query(1, gt=0),
                    page_size: int = Query(100, gt=0),
                    sort: Optional[str] = None,
                    genre: Optional[str] = None,
                    film_service: FilmService = Depends(get_film_service)) -> list[FilmListSerializer]:
    """
    Метод возвращает сериализованный список фильмов, с опциональной фильтрацией по жанру.
    В случае отсутствия подходяших фильмов - возвращает код ответа 404
    :param page_number: номер страницы
    :param page_size: размер станицы
    :param sort: поле, по которому ссортируется список
    :param genre: жанр, по которому фильтруется список фильмов'''
    """

    sort = await validation_index_model_fiield(sort)
    start_index = (page_number - 1) * page_size

    film_list = await film_service.get_list_film(start_index, page_size, sort, genre)

    if not film_list:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return [FilmListSerializer(**dict(film)) for film in film_list]
