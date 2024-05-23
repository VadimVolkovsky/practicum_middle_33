import asyncio

import aiohttp
import pytest_asyncio
from httpx import AsyncClient

from elasticsearch import AsyncElasticsearch
from main import app
from tests.functional.settings import test_settings


@pytest_asyncio.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(
        hosts=test_settings.elastic_host,
        verify_certs=False,
        use_ssl=False
    )
    yield client
    await client.close()


@pytest_asyncio.fixture(scope='session')
async def async_client():
    async with AsyncClient(app=app, base_url=test_settings.service_url) as client:
        yield client


@pytest_asyncio.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def api_session(event_loop):
    session = aiohttp.ClientSession()
    yield session
    await session.close()
