import json
from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import BaseModel
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from services.proto_service import ProtoService
from services.utils import _get_query_body


FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService(ProtoService):

    async def get_list_film(self,
                            start_index: int,
                            page_size: int,
                            sort: str = None,
                            genre: str = None,
                            query: str = None) -> Optional[list[Film]]:
        """
        Метод возвращает список фильмов подходящих под указанные параметры.
        В случае отсутствия подходящих фильмов - возвращает None.
        """

        parameters = str({
            "start_index": start_index,
            "page_size": page_size,
            "sort": sort,
            "genre": genre,
            "query": query
        })

        film_list = await self._get_films_from_cache(parameters)

        if not film_list:
            film_list = await self._get_list_film_from_elastic(start_index, page_size, sort, genre, query)

            if not film_list:
                return None

            await self._put_films_to_cache(parameters, film_list)
        return film_list

    async def _get_list_film_from_elastic(self,
                                          start_index: int,
                                          page_size: int,
                                          sort: Optional[str] = None,
                                          genre: Optional[str] = None,
                                          query: Optional[str] = None) -> Optional[list[Film]]:
        """
        Вспомогательный метод для получения списка фильмов из ElasticSearch,
        соответствующих указанным параметрам.
        В случае отсутствия подходящих фильмов - возвращает None.
        """

        query_body = await _get_query_body(start_index, page_size, sort, genre, query)

        try:
            search = await self.elastic.search(index='movies', body=query_body)
        except NotFoundError:
            return None

        list_film = [
            Film(**hit['_source']) for hit in search['hits']['hits']
        ]

        return list_film

    async def _get_films_from_cache(self, parameters: str) -> Optional[list[Film]]:
        """
        Получаем фильмы из кэша. Если фильмов в кэше нет - возвращаем None
        """

        data = await self.redis.get(parameters)
        if not data:
            return None

        data = data.decode()
        films = [Film.parse_raw(json.dumps(film)) for film in json.loads(data)]
        return films

    async def _put_films_to_cache(self, parameters: str, films: list[Film]):
        """
        Сохраняем данные о Фильмах в кэш, сериализуя модель через pydantic в формат json.
        """
        value = ','.join([film.json() for film in films])
        await self.redis.set(parameters, '[' + value + ']', FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """
    Провайдер FilmService
    Используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
    """
    return FilmService(redis, elastic)
