from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from services.proto_service import ProtoService
from services.utils import _get_query_body


class FilmService(ProtoService):

    async def get_list_film(self,
                            start_index: int,
                            page_size: int,
                            sort: str = None,
                            genre: [str | list[str]] = None,
                            query: str = None,
                            ) -> Optional[list[Film]]:
        """
        Метод возвращает список фильмов подходящих под указанные параметры.
        В случае отсутствия подходящих фильмов - возвращает None.
        """

        model = Film
        parameters = self.get_params_to_cache(
            start_index=start_index,
            page_size=page_size,
            sort=sort,
            genre=genre,
            query=query,
            model=model
        )
        film_list = await self._get_objs_from_cache(parameters, model)

        if not film_list:
            film_list = await self._get_list_film_from_elastic(start_index, page_size, sort, genre, query)

            if not film_list:
                return None

            await self._put_objs_to_cache(parameters, film_list)
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

        query_body = await _get_query_body(start_index=start_index, page_size=page_size, sort=sort, genre=genre,
                                           query=query)

        try:
            search = await self.elastic.search(index='movies', body=query_body)
        except NotFoundError:
            return None

        list_film = [
            Film(**hit['_source']) for hit in search['hits']['hits']
        ]

        return list_film


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
