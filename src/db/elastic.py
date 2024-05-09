from enum import Enum
from typing import Optional

from elasticsearch import AsyncElasticsearch
from models.film import Film
from models.genre import Genre

es: Optional[AsyncElasticsearch] = None


async def get_elastic() -> AsyncElasticsearch:
    return es


class Indexes(Enum):
    movies = {'index_name': 'movies',
              'index_model': Film}
    genres = {'index_name': 'genres',
              'index_model': Genre}
