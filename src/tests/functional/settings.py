from pydantic_settings import BaseSettings
from pydantic import Field


class TestSettings(BaseSettings):
    elastic_host: str = Field('elasticsearch:9200', env='ELASTIC_HOST')
    service_url: str = 'http://api:8000'
    redis_host: str = 'redis'
    redis_port: int = 6379

    # для локального дебага тестов
    # es_host: str = Field('127.0.0.1:9200', env='ELASTIC_HOST')
    # service_url: str = 'http://127.0.0.1:8000'
    # redis_host: str = '127.0.0.1'
    # redis_port: int = 6379

    class Config:
        env_file = '.env'

test_settings = TestSettings()
