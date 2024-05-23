from functools import lru_cache

import backoff
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from constants import OptStrType
from db.elastic import get_elastic
from db.redis import get_redis
from models.models import Film
from models.models import Person
from services.exceptions import CONNECTION_EXCEPTIONS
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

    @backoff.on_exception(backoff.expo, CONNECTION_EXCEPTIONS)
    async def get_person_films_from_elastic(self,
                                            start_index: int,
                                            page_size: int,
                                            sort: OptStrType = None,
                                            person: OptStrType = None,
                                            query: OptStrType = None) -> list[Film] | None:
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
    async def filter_films_by_person_with_role(films: list[Film] | list, person: Person) -> list[dict[str, str]]:
        """
        Фильтрует список фильмов в которых персонаж принимал участие,
        с указанием его ролей. Возвращает пустой список, если персонаж еще не принимал участие в фильмах.
        """
        films_by_person = []
        if films:
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
                               sort: OptStrType = None,
                               query: OptStrType = None) -> list[Person] | None:
        """Поиск персонажей по имени с учетом возможных опечаток"""

        model = Person
        parameters = self.get_params_to_cache(
            start_index=start_index,
            page_size=page_size,
            sort=sort,
            query=query,
            model=model
        )
        persons_data = await self._get_objs_from_cache(parameters, model)

        if not persons_data:
            persons_data = await self._get_list_persons_from_elastic(start_index, page_size, sort, query)

            if not persons_data:
                return None

            await self._put_objs_to_cache(parameters, persons_data)
        return persons_data

    @backoff.on_exception(backoff.expo, CONNECTION_EXCEPTIONS)
    async def _get_list_persons_from_elastic(self,
                                             start_index: int,
                                             page_size: int,
                                             sort: OptStrType = None,
                                             query: OptStrType = None) -> list[Person] | None:
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
