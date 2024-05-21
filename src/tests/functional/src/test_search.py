import logging
import os

import aiohttp
import pytest

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
async def test_search(es_write_data, get_es_data, query_data, expected_answer):
    # 1. Генерируем данные для ES
    es_data = await get_es_data()

    # 2. Загружаем данные в ES
    await es_write_data(es_data)

    # 3. Запрашиваем данные из ES по API
    url = test_settings.service_url + '/api/v1/films/search'
    query_params = query_data

    session = aiohttp.ClientSession()
    async with session.get(url, params=query_params) as response:
        body = await response.json()
        status = response.status
    await session.close()

    # async with api_session.get(url, params=query_params) as response:
    #     body = await response.json()
    #     status = response.status
    # response = await get_request(url, query_params)

    # 4. Проверяем ответ
    assert status == expected_answer['status']
    assert len(body) == expected_answer['count']
