import logging
from contextlib import asynccontextmanager

import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from core.config import app_settings
from core.logger import LOGGING
from db import redis, elastic
from api.v1.routers import main_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = Redis(host=app_settings.redis_host, port=app_settings.redis_port)
    elastic.es = AsyncElasticsearch(hosts=[f'{app_settings.elastic_host}:{app_settings.elastic_port}'])
    yield
    await redis.redis.close()
    await elastic.es.close()


app = FastAPI(
    title=app_settings.project_name,
    description="Информация о фильмах, жанрах и людях, участвовавших в создании произведения",
    version="1.0.0",
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)


# @app.on_event('startup')
# async def startup():
#     redis.redis = Redis(host=app_settings.redis_host, port=app_settings.redis_port)
#     elastic.es = AsyncElasticsearch(hosts=[f'{app_settings.elastic_host}:{app_settings.elastic_port}'])
#
#
# @app.on_event('shutdown')
# async def shutdown():
#     await redis.redis.close()
#     await elastic.es.close()

app.include_router(main_router, prefix='/api/v1')

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
