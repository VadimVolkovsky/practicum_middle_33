from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from services.utils import _get_query_body


FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        '''функция для получения экземпляра фильма по id. Возвращает None если фильм отсутствует в базе данных'''

        film = await self._film_from_cache(film_id)

        if not film:
            film = await self._get_film_from_elastic(film_id)

            if not film:
                return None

            await self._put_film_to_cache(film)

        return film

    async def get_list_film(self,
                            start_index: int,
                            end_index: int,
                            sort: str = None,
                            genre: str = None,
                            query: str = None) -> Optional[list[Film]]:
        '''Функция для получения списка фильмов, используя параметры фильтрации и сортировки.
        Сначала поиск ведется в кэше, если в кэше нет нужных данных - поиск ведется в ES
        Возвращает None, если в базе нет фильмов с указанными парамметрами поиска'''

        # film_list = await self._list_film_from_cache()
        film_list = None

        if not film_list:
            film_list = await self._get_list_film_from_elastic(start_index, end_index, sort, genre, query)

            if not film_list:
                return None

            # await self._put_film_to_cache(list_film)
        return film_list

    async def _get_list_film_from_elastic(self,
                                          start_index: int,
                                          page_size: int,
                                          sort: Optional[str] = None,
                                          genre: Optional[str] = None,
                                          query: Optional[str] = None) -> Optional[list[Film]]:
        '''Функция для получения списка фильмов, используя параметры фильтрации и сортировки из ES.
        Возвращает список фильмов, если они есть в ES, если нет - None'''

        query_body = await _get_query_body(start_index, page_size, sort, genre, query)

        try:
            search = await self.elastic.search(index='movies', body=query_body)
        except NotFoundError:
            return None

        list_film = [
            Film(**hit['_source']) for hit in search['hits']['hits']
        ]

        return list_film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        '''Функция для получения экземпляра фильма по id из ES.
        Возвращает экземпляр фильма, если они есть в ES, если нет - None'''

        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            return None

        return Film(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        '''Функция для получения экземпляра фильма по id из кэша.
        Возвращает экземпляр фильма, если они есть в кеше, если нет - None'''

        data = await self.redis.get(film_id)

        if not data:
            return None

        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        '''Функция для сохранения данных о фильме в кэш'''

        await self.redis.set(film.id, film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)


# get_film_service — это провайдер FilmService.
# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# Используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
