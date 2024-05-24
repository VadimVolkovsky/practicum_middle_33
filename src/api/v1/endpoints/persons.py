from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db.elastic import Indexes
from services.person import PersonService, get_person_service
from api.v1.paginate_params import PaginatedParams, get_paginated_params


router = APIRouter()


class PersonFilmsRoles(BaseModel):
    """Модель для отображения ролей персонажа в фильме"""
    id: str
    roles: list[str]


class PersonSerializer(BaseModel):
    """Модель для отображения информации о персонаже с учетом его ролей в фильмах"""
    id: str
    name: str = Field(..., alias='full_name')
    films: list[PersonFilmsRoles] | None = None

    class Config:
        populate_by_name = True


class PersonFilmsSerializer(BaseModel):
    """Модель для отображения фильмов, в которых принял участие персонаж"""
    id: str
    title: str
    imdb_rating: float | None = None


@router.get('/search', response_model=list[PersonSerializer],
            description="""Выполните запрос на поиск персонажа по имени, где:
            query: строка, по которой производится полнотекстовый поиск
            page_number: номер страницы
            page_size: размер станицы
            sort: поле, по которому ссортируется список

            В ответе будет выведен список персонажей"""
            )
async def persons_search(query: str,
                         paginated: PaginatedParams = Depends(get_paginated_params),
                         person_service: PersonService = Depends(get_person_service)) -> list[PersonSerializer]:
    '''Метод для поиска подходящих по имени персонажей
    :param query: строка, по которой производится полнотекстовый поиск
    :param page_number: номер страницы
    :param page_size: размер станицы
    :param sort: поле, по которому ссортируется список
    :param person_service: '''
    page_number = paginated.get_page_number()
    page_size = paginated.get_page_size()
    start_index = (page_number - 1) * page_size
    persons_data = await person_service.get_list_persons(start_index, page_size, query=query)

    if not persons_data:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')

    persons_data_with_films = []
    for person in persons_data:
        films_data = await person_service.get_person_films_by_id(person)
        films_by_person = await person_service.filter_films_by_person_with_role(films_data, person)
        person_data = person.dict()
        person_data['films'] = films_by_person
        persons_data_with_films.append(person_data)
    return [PersonSerializer(**dict(person)) for person in persons_data_with_films]


@router.get('/{person_id}', response_model=PersonSerializer,
            description="""Выполните запрос на поиск персонажа по его id,
            в ответе будет выведен подробная информация о персонаже, со списком его фильмов и ролей""")
async def person_detail(
        person_id: str,
        person_service: PersonService = Depends(get_person_service)
) -> PersonSerializer:
    """Получение информации о персонаже, со списком его фильмов и ролей"""
    try:
        index_dict = Indexes.persons.value
        person = await person_service.get_by_id(person_id, index_dict)
        films_data = await person_service.get_person_films_by_id(person=person)
    except KeyError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='index not found')

    films_by_person = await person_service.filter_films_by_person_with_role(films_data, person)
    person_data = person.dict()
    person_data['films'] = films_by_person
    return PersonSerializer(**person_data)


@router.get('/{person_id}/film', response_model=list[PersonFilmsSerializer],
            description="""Выполните запрос на поиск персонажа по его id,
            в ответе будет выведен информация о фильмах, в которых принял участие персонаж""")
async def person_films_detail(
        person_id: str,
        person_service: PersonService = Depends(get_person_service)
) -> list[PersonFilmsSerializer]:
    """Получение информации о фильмах, в которых принял участие персонаж"""
    index_dict = Indexes.persons.value
    person = await person_service.get_by_id(person_id, index_dict)
    persons_films = await person_service.get_person_films_by_id(person)
    return [PersonFilmsSerializer(**film.dict()) for film in persons_films]
