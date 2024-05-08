from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from pydantic import BaseModel
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

    async def get_by_id(self, film_id: str, index_dict: dict[str, BaseModel]) -> Optional[Film]:
        """
        Метод возвращает объект по id.
        В случае отсутствия объекта с указанным id - возвращает None
        """
        index_name = index_dict.get('index_name')
        index_model = index_dict.get('index_model')

        instance = await self._film_from_cache(film_id)

        if not instance:
            instance = await self._get_instance_from_elastic(film_id, index_name, index_model)

            if not instance:
                return None

            await self._put_film_to_cache(instance)

        return instance

    async def get_list_film(self,
                            start_index: int,
                            end_index: int,
                            sort: str = None,
                            genre: str = None,
                            query: str = None) -> Optional[list[Film]]:
        """
        Метод возвращает список фильмов подходящих под указанные параметры.
        В случае отсутствия подходящих фильмов - возвращает None.
        """

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

    async def _get_instance_from_elastic(self, film_id: str, index_name: str, index_model: BaseModel) -> Optional[Film]:
        """
        Вспомогательный метод для получения фильма из ElasticSearch по его id.
        В случае отсутствия подходящего фильма - возвращает None.
        """
        try:
            doc = await self.elastic.get(index=index_name, id=film_id)
        except NotFoundError:
            return None

        return index_model(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        """
        Получаем данные о фильме из кэша.
        Если фильма в кэше нет - возвращаем None
        """
        data = await self.redis.get(film_id)

        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        """
        Сохраняем данные о фильме в кэш, сериализуя модель через pydantic в формат json.
        """
        await self.redis.set(film.id, film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)


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
