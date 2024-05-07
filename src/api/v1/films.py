from datetime import datetime
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.film import FilmService, get_film_service

# Объект router, в котором регистрируем обработчики
router = APIRouter()

# FastAPI в качестве моделей использует библиотеку pydantic
# https://pydantic-docs.helpmanual.io
# У неё есть встроенные механизмы валидации, сериализации и десериализации
# Также она основана на дата-классах


# Модель ответа API
class FilmListSerializer(BaseModel):
    id: str
    title: str
    imdb_rating: float


class FilmSerializer(FilmListSerializer):
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
                      film_service: FilmService = Depends(get_film_service)) -> FilmListSerializer:
    start_index = (page_number - 1) * page_size

    film_list = await film_service.get_list_film(start_index, page_size, sort=sort, query=query)

    if not film_list:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    # return FilmListSerializer(*film_list)
    return film_list


@router.get('/{film_id}', response_model=FilmSerializer)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> FilmSerializer:
    film = await film_service.get_by_id(film_id)

    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return FilmSerializer(id=film.id, title=film.title)


@router.get('', response_model=list[FilmListSerializer])
async def film_list(page_number: int = Query(1, gt=0),
                    page_size: int = Query(100, gt=0),
                    sort: Optional[str] = None,
                    genre: Optional[str] = None,
                    film_service: FilmService = Depends(get_film_service)) -> FilmListSerializer:
    # Применяем пагинацию
    start_index = (page_number - 1) * page_size
    # end_index = start_index + page_size

    film_list = await film_service.get_list_film(start_index, page_size, sort, genre)

    if not film_list:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    # return FilmListSerializer(*film_list)
    return film_list
