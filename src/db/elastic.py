from enum import Enum

from elasticsearch import AsyncElasticsearch
from models.models import Film, Genre, Person

es: AsyncElasticsearch | None = None


async def get_elastic() -> AsyncElasticsearch:
    return es


class Indexes(Enum):
    movies = {'index_name': 'movies',
              'index_model': Film}
    genres = {'index_name': 'genres',
              'index_model': Genre}
    persons = {'index_name': 'persons',
               'index_model': Person}
