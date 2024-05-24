from abc import ABC, abstractmethod
from functools import cache
from typing import Any, Type, Callable

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from services.film import get_film_service

dependencies_container: dict[Type | Callable, Callable] = {}


def add_factory_to_mapper(class_: Type | Callable):
    def _add_factory_to_mapper(func: Callable):
        dependencies_container[class_] = func
        return func
    return _add_factory_to_mapper


class SearchServiceABC(ABC):
    @abstractmethod
    async def get_search_service(self) -> Any:
        pass


class ElasticsearchService(SearchServiceABC):
    async def get_search_service(self) -> AsyncElasticsearch:
        return await get_elastic()


@add_factory_to_mapper(SearchServiceABC)
@cache
def create_search_service() -> ElasticsearchService:
    return ElasticsearchService()
