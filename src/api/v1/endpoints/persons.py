from http import HTTPStatus
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.person import PersonService, get_person_service

router = APIRouter()


class PersonFilmsRoles(BaseModel):
    """Модель для отображения ролей персонажа в фильме"""
    id: str
    roles: list[str]


class PersonSerializer(BaseModel):
    """Модель для отображения информации о персонаже с учетом его ролей в фильмах"""
    id: str
    name: str = Field(..., alias='full_name')
    films: Optional[list[PersonFilmsRoles]]

    class Config:
        allow_population_by_field_name = True


class PersonFilmsSerializer(BaseModel):
    """"""
    id: str
    title: str
    imdb_rating: Optional[float]


@router.get('/{person_id}', response_model=PersonSerializer)
async def person_detail(
        person_id: str,
        person_service: PersonService = Depends(get_person_service)
) -> PersonSerializer:
    """Получение информации о персонаже, со списком его фильмов и ролей"""
    person_with_films = await person_service.get_by_id(person_id)

    if not person_with_films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return PersonSerializer(**person_with_films)


@router.get('/{person_id}/film', response_model=list[PersonFilmsSerializer])
async def person_films_detail(
        person_id: str,
        person_service: PersonService = Depends(get_person_service)
) -> list[PersonFilmsSerializer]:
    """"""
    persons_films = await person_service.get_person_films_by_id(person_id)

    if not persons_films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return [PersonFilmsSerializer(**film.dict()) for film in persons_films]