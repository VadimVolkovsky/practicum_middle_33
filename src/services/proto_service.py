from http import HTTPStatus
from fastapi import HTTPException
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import BaseModel
from redis.asyncio import Redis

from models.film import Film
from models.genre import Genre
from models.person import Person


CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class ProtoService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, obj_id: str, index_dict: dict[str, BaseModel | str]) -> Optional[Film | Genre | Person]:
        """
        Метод возвращает объект по id.
        В случае отсутствия объекта с указанным id - возвращает None
        """
        index_name = index_dict.get('index_name')
        index_model = index_dict.get('index_model')

        instance = await self._get_obj_from_cache(obj_id, index_model)

        if not instance:
            instance = await self._get_instance_from_elastic(obj_id, index_name, index_model)

            if not instance:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Object {obj_id} not found')

            await self._put_obj_to_cache(instance)

        return instance

    async def _get_obj_from_cache(self, obj_id: str, index_model: Film | Genre | Person) -> Optional[Film | Genre | Person]:
        """
        Получаем данные об объекте из кэша.
        Если объекта в кэше нет - возвращаем None
        """
        data = await self.redis.get(obj_id)

        if not data:
            return None

        obj = index_model.parse_raw(data)
        return obj

    async def _get_instance_from_elastic(self, obj_id: str, index_name: str, index_model: BaseModel) -> Optional[Film]:
        """
        Вспомогательный метод для получения объекта из ElasticSearch по его id.
        В случае отсутствия подходящего объекта - возвращает None.
        """
        try:
            doc = await self.elastic.get(index=index_name, id=obj_id)
        except NotFoundError:
            return None

        return index_model(**doc['_source'])

    async def _put_obj_to_cache(self, obj: Film | Genre | Person):
        """
        Сохраняем данные о объекте в кэш, сериализуя модель через pydantic в формат json.
        """
        await self.redis.set(obj.id, obj.json(), CACHE_EXPIRE_IN_SECONDS)
