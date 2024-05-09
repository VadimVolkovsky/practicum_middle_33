from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.elastic import Indexes
from services.film import FilmService, get_film_service

router = APIRouter()


class GenreSerializer(BaseModel):
    '''модель для возврата экземпляра жанра из API'''

    id: str
    name: str


@router.get('/{genre_id}', response_model=GenreSerializer)
async def film_details(genre_id: str, film_service: FilmService = Depends(get_film_service)) -> GenreSerializer:
    """
    Метод возвращает сериализованный объект фильма по id.
    В случае отсутствия фильма с указанным id - возвращает код ответа 404
    :param film_id: id экземпляра фильма
    """
    try:
        index_dict = Indexes.genres.value
        genre = await film_service.get_by_id(genre_id, index_dict)

        if not genre:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genres not found')

        return GenreSerializer(**dict(genre))

    except KeyError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='index not found')
