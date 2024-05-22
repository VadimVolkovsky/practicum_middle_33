import logging
import os

import pytest

from db.elastic import Indexes
from schemas.es_schemas import elastic_film_index_schema
from tests.functional.settings import test_settings


logger = logging.getLogger(os.path.basename(__file__))


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        ({'query': 'Repurpose'}, {'status': 200, 'count': 1}),
        ({'query': 'Billy Montes'}, {'status': 200, 'count': 1}),
        ({'query': 'Melodrama'}, {'status': 200, 'count': 4}),
        ({'query': 'Detective', 'page_size': 4}, {'status': 200, 'count': 4}),
        ({'query': ''}, {'status': 200, 'count': 10}),
        ({'query': 'test_test'}, {'status': 404, 'count': 1}),
    ]
)
@pytest.mark.asyncio
async def test_search(es_write_data, get_es_data, query_data, expected_answer, get_request):
    es_index = Indexes.movies.value.get('index_name')
    es_data = await get_es_data(es_index)

    await es_write_data(es_index=es_index, data=es_data, es_index_schema=elastic_film_index_schema)

    url = test_settings.service_url + '/api/v1/films/search'
    query_params = query_data

    response = await get_request(url, params=query_params)
    status = response.status
    body = response.body

    assert status == expected_answer['status']
    assert len(body) == expected_answer['count']
