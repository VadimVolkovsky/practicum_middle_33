import json
from http import HTTPStatus
from fastapi import HTTPException

from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import BaseModel
from redis.asyncio import Redis

from models.models import Film, Genre, Person

CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class ProtoService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(
            self, obj_id: str,
            index_dict: dict[str, BaseModel | str]
    ) -> Film | Genre | Person | None:
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

    async def _get_instance_from_elastic(
            self, obj_id: str,
            index_name: str,
            index_model: BaseModel
    ) -> Film | Genre | Person | None:
        """
        Вспомогательный метод для получения объекта из ElasticSearch по его id.
        В случае отсутствия подходящего объекта - возвращает None.
        """
        try:
            doc = await self.elastic.get(index=index_name, id=obj_id)
        except NotFoundError:
            return None

        return index_model(**doc['_source'])  # noqa

    @staticmethod
    def get_params_to_cache(**kwargs):
        return str(kwargs)

    async def _get_obj_from_cache(
            self, obj_id: str,
            index_model: BaseModel
    ) -> BaseModel | None:
        """
        Получаем данные об объекте из кэша. Если объекта в кэше нет - возвращаем None
        """

        data = await self.redis.get(obj_id)

        if not data:
            return None

        obj = index_model.parse_raw(data)
        return obj

    async def _put_obj_to_cache(self, obj: Film | Genre | Person):
        """
        Сохраняем данные об объекте в кэш, сериализуя модель через pydantic в формат json.
        """
        key_for_redis = str( dict(name="Returning one object", id=obj.id, class_name=obj.__class__))
        await self.redis.set(key_for_redis, obj.json(), CACHE_EXPIRE_IN_SECONDS)

    async def _get_objs_from_cache(
            self, parameters: str,
            model: Film | Genre | Person
    ) -> list[Film | Genre | Person] | None:
        """Получаем объекты из кэша. Если объектов в кэше нет - возвращаем None"""
        data = await self.redis.get(parameters)
        if not data:
            return None
        data = data.decode()
        objs = [model.parse_raw(json.dumps(obj)) for obj in json.loads(data)]
        return objs

    async def _put_objs_to_cache(self, parameters: str, objs: list[Film | Genre | Person]):
        """
        Сохраняем данные об объектах в кэш, сериализуя модель через pydantic в формат json.
        """
        value = '[' + ','.join([obj.json() for obj in objs]) + ']'
        key_for_redis = dict(name="Returning a list of objects", class_name=objs[0].__class__, parameters=parameters)
        await self.redis.set(key_for_redis, value, CACHE_EXPIRE_IN_SECONDS)
