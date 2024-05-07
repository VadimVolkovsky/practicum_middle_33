from typing import Optional


async def _get_query_body(start_index: int,
                          page_size: int,
                          sort: Optional[str] = None,
                          genre: Optional[str] = None,
                          query: Optional[str] = None) -> dict:
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
