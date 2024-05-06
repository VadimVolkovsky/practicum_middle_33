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
class Film(BaseModel):
    id: str
    title: str


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)

    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return Film(id=film.id, title=film.title)


@router.get('', response_model=list[FilmList])
async def read_books(page_number: int = Query(1, gt=0),
                     page_size: int = Query(10, gt=0),
                     sort: Optional[str] = None,
                     genre: Optional[str] = None,
                     film_service: FilmService = Depends(get_film_service)):
    # Применяем пагинацию
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size

    # paginated_list = books_db[start_index:end_index]

    film_list = await film_service.get_list_film()

    # Применяем сортировку, если указана
    if sort and sort == 'imdb_rating':
        film_list = sorted(film_list, key=lambda film: -film.imdb_rating if sort.startswith('-') else film.imdb_rating)

    # people.sort(key=lambda person: (
    #     -person.firstname,
    #     person.lastname,
    #     person.weight,
    # ))
    return film_list
