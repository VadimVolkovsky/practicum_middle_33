import logging
import os

from constants import OptStrType
from models.models import BaseNameModel, Person

logger = logging.getLogger(os.path.basename(__file__))


async def _get_query_body(start_index: int,
                          page_size: int,
                          sort: OptStrType = None,
                          genre: OptStrType = None,
                          query: OptStrType = None,
                          person_id: OptStrType = None,
                          model: BaseNameModel | None = None) -> dict:
    '''функция для составления запроса поиска в elassticsearch
    :param start_index: номер записи с которой начинается выдача записей с ES
    :param page_size: размер станицы
    :param genre: жанр, по которому фильтруется список фильмов
    :param person_id: айди персонажа, по которому фильтруется список фильмов
    :param sort: поле, по которому ссортируется список'''

    body = {
        'size': page_size,
        'from': start_index,
    }

    if sort:
        if sort.startswith('-'):
            sort = sort.replace('-', '')
            body['sort'] = [{sort: {'order': 'desc'}}]
        else:
            body['sort'] = [{sort: {'order': 'asc'}}]

    if genre:
        if not body.get('query', None):
            body['query'] = {}

        # if isinstance(genre, list) and len(genre) > 1:
        #     search_query = [{'term': {'genre.id': g}} for g in list(genre)]
        # else:
        #     search_query = {'term': {'genre.id': genre[0] if isinstance(genre, list) else genre}}

        body['query']['nested'] = {
            'path': 'genre',
            # 'query': {*search_query} if isinstance(search_query, list) else **search_query,
            'query': {'term': {'genre.id': genre}},
            'inner_hits': {
            }
        }

    if person_id:
        if not body.get('query', None):
            body['query'] = {}

        body = {
            "query": {
                'bool': {
                    'should': [
                        {"nested": {
                            "path": "directors",
                            "query": {
                                "bool": {
                                    "must": [
                                        {"match": {"directors.id": person_id}},
                                    ]
                                }
                            }
                        }
                        },
                        {"nested": {
                            "path": "actors",
                            "query": {
                                "bool": {
                                    "must": [
                                        {"match": {"actors.id": person_id}},
                                    ]
                                }
                            }
                        }
                        },
                        {"nested": {
                            "path": "writers",
                            "query": {
                                "bool": {
                                    "must": [
                                        {"match": {"writers.id": person_id}},
                                    ]
                                }
                            }
                        }
                        }
                    ]
                }
            }
        }

    # if person_id:  # TODO нужно доработать т.к. возвращает только первый фильм персонажа на эндпоинте /{person_id}/
        # if not body.get('query', None):
        #     body['query'] = {}
        # body['query']['bool'] = {
        #     'should': [
        #         {
        #             "nested": {
        #                 "path": field,
        #                 "query": {
        #                     "bool": {
        #                         "must": [
        #                             {"match": {f"{field}.id": person_id}},
        #                         ]
        #                     }
        #                 }
        #             }
        #         }
        #         for field in ["directors", "actors", "writers"]
        #     ],
        # }

    if query and model is Person:
        if not body.get('query', None):
            body['query'] = {}

        body['query']['multi_match'] = {
            'query': query,
            'fields': ['title', 'name', 'actors.name', 'writers.name', 'directors.name', 'genre.name', 'description'],
            'fuzziness': 'AUTO'
        }

    elif query:
        if not body.get('query', None):
            body['query'] = {}

        body['query']['bool'] = {
            "should": [
                *[
                    {
                        "nested": {
                            "path": f"{field}",
                            "query": {
                                "multi_match": {
                                    "query": query,
                                    "fields": [f"{field}.name"]
                                }
                            }
                        }
                    }
                    for field in ["directors", "actors", "writers", 'genre']
                ],
                {
                    "multi_match": {
                        "query": query,
                        "fields": ['title', 'name', 'description']
                    }
                }
            ]
        }

    return body


async def validation_index_model_field(sort_field: OptStrType, index_model) -> None:
    """Проверяет, что указанное поле подходит для сортировки"""
    if index_model and sort_field and sort_field not in index_model.__fields__.keys():
        return None

    return sort_field
