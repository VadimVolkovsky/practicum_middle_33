from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.person import PersonService, get_person_service, PersonsFilms

router = APIRouter()


class PersonSerializer(BaseModel):
    id: str
    name: str = Field(..., alias='full_name')
    films: Optional[list[PersonsFilms]]

    class Config:
        allow_population_by_field_name = True


@router.get('/{person_id}', response_model=PersonSerializer)
async def person_detail(person_id: str,
                        person_service: PersonService = Depends(get_person_service)) -> PersonSerializer:
    """Получение информации о персонаже, со списком его фильмов и ролей"""
    person_with_films = await person_service.get_by_id(person_id)

    if not person_with_films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return PersonSerializer(**person_with_films)
