from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import BaseModel
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from models.person import Person
from services.utils import _get_query_body


CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
ROLES = {
    'directors': 'director',
    'actors': 'actor',
    'writers': 'writer'
}


class PersonsFilms(BaseModel):
    id: str
    roles: list[str]


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[dict]:
        """"""
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)
        films_by_person = await self._get_person_films_from_elastic(start_index=1, page_size=100, person=person)
        person_data = person.dict()
        person_data['films'] = films_by_person
        return person_data

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        """
        Получаем данные о персоналии из кэша.
        Если персоналии в кэше нет - возвращаем None
        """
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index='persons', id=person_id)
        except NotFoundError:
            return None
        return Person(**doc['_source'])

    async def _get_person_films_from_elastic(self,
                                             start_index: int,
                                             page_size: int,
                                             sort: Optional[str] = None,
                                             person: Optional[Person] = None,
                                             query: Optional[str] = None):
        """"""
        query_body = await _get_query_body(
            start_index=start_index,
            page_size=page_size,
            sort=sort,
            person_id=person.id,
            query=query)

        try:
            search = await self.elastic.search(index='movies', body=query_body)
        except NotFoundError:
            return None

        list_film: list[Film] = [
            Film(**hit['_source']) for hit in search['hits']['hits']
        ]

        films_by_person = await self._filter_films_by_person(list_film, person)
        return films_by_person

    @staticmethod
    async def _filter_films_by_person(films: list[Film], person: Person) -> list[dict[str, str]]:
        """
        Возвращает список фильмов в которых персонаж принимал участие,
        с указанием его ролей
        """
        films_by_person = []
        for film in films:
            film_with_roles = {'id': film.id, 'roles': []}
            for roles, role in ROLES.items():
                for role_obj in getattr(film, roles):
                    if role_obj['id'] == person.id:
                        film_with_roles['roles'].append(role)
                        break
            films_by_person.append(film_with_roles)
        return films_by_person

    async def _put_person_to_cache(self, person: Person):
        """
        Сохраняем данные о person в кэш, сериализуя модель через pydantic в формат json.
        """
        await self.redis.set(person.id, person.json(), CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """
    Провайдер PersonService
    Используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
    """
    return PersonService(redis, elastic)
