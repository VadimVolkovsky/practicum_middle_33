from typing import Optional

from db.elastic import Indexes


async def _get_query_body(start_index: int,
                          page_size: int,
                          sort: Optional[str] = None,
                          genre: Optional[str] = None,
                          query: Optional[str] = None) -> dict:
    '''функция для составления запроса поиска в elassticsearch
    :param start_index: номер записи с которой начинается выдача записей с ES
    :param page_size: размер станицы
    :param genre: жанр, по которому фильтруется список фильмов
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

        body['query']['nested'] = {
            'path': 'genre',
            'query': {
                'term': {
                    'genre.id': genre
                }
            },
            'inner_hits': {
            }
        }

    if query:
        if not body.get('query', None):
            body['query'] = {}

        body['query']['multi_match'] = {
            'query': query,
            'fields': ['title', 'actors.name', 'writers.name', 'directors.name', 'genre.name', 'description'],
            'fuzziness': 'AUTO'
        }

    return body


async def validation_index_model_fiield(sort_field: Optional[str]) -> None:
    index_model = Indexes.movies.value.get('index_model', None)

    if index_model and sort_field and sort_field not in index_model.__fields__.keys():
        return None

    return sort_field
