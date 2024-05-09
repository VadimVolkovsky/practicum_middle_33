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
from services.proto_service import ProtoService
from services.utils import _get_query_body

ROLES = {
    'directors': 'director',
    'actors': 'actor',
    'writers': 'writer'
}


class PersonService(ProtoService):
    async def get_person_films_by_id(self, person: Person):
        """Сервис для получения информации о фильмах, в которых персонаж принимал участие"""
        films_data = await self.get_person_films_from_elastic(start_index=1, page_size=100, person=person)
        return films_data

    async def get_person_films_from_elastic(self,
                                            start_index: int,
                                            page_size: int,
                                            sort: Optional[str] = None,
                                            person: Optional[Person] = None,
                                            query: Optional[str] = None) -> Optional[list[Film]]:
        """Получаем список фильмов персонажа из ElasticSearch"""
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

        films_data = [
            Film(**hit['_source']) for hit in search['hits']['hits']
        ]
        return films_data

    @staticmethod
    async def filter_films_by_person_with_role(films: list[Film], person: Person) -> list[dict[str, str]]:
        """
        Фильтрует список фильмов в которых персонаж принимал участие,
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

    async def get_list_persons(self,
                               start_index: int,
                               page_size: int,
                               sort: str = None,
                               query: str = None) -> Optional[list[Person]]:
        """Поиск персонажей по имени с учетом возможных опечаток"""
        # TODO get_persons_from_cache
        persons_data = await self._get_list_persons_from_elastic(start_index, page_size, sort, query)
        if not persons_data:
            return None
        # TODO put_persons_to_cache
        return persons_data

    # TODO вроде можно объеденить с _get_list_film_from_elastic и вынести в протосервис
    async def _get_list_persons_from_elastic(self,
                                             start_index: int,
                                             page_size: int,
                                             sort: Optional[str] = None,
                                             query: Optional[str] = None) -> Optional[list[Person]]:
        """"""
        query_body = await _get_query_body(start_index, page_size, sort, query=query)

        try:
            search = await self.elastic.search(index='persons', body=query_body)
        except NotFoundError:
            return None

        persons_data = [
            Person(**hit['_source']) for hit in search['hits']['hits']
        ]

        return persons_data


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
