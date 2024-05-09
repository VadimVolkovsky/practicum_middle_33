from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.elastic import Indexes
from services.genre import GenreService, get_genre_service

router = APIRouter()


class GenreSerializer(BaseModel):
    """модель для возврата экземпляра жанра из API"""

    id: str
    name: str


@router.get('/{genre_id}', response_model=GenreSerializer)
async def genre_details(genre_id: str, genre_service: GenreService = Depends(get_genre_service)) -> GenreSerializer:
    """
    Метод возвращает сериализованный объект жанра по id.
    В случае отсутствия жанра с указанным id - возвращает код ответа 404
    """
    try:
        index_dict = Indexes.genres.value
        genre = await genre_service.get_by_id(genre_id, index_dict)

        if not genre:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

        return GenreSerializer(**dict(genre))

    except KeyError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='index not found')
