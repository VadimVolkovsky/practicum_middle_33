from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from services.proto_service import ProtoService


class GenreService(ProtoService):
    pass


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """
    Провайдер GenreService
    Используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
    """
    return GenreService(redis, elastic)
