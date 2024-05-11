import os
from logging import config as logging_config

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)
load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppSettings(BaseSettings):
    project_name: str = 'movies'
    redis_host: str = Field(default='redis')
    redis_port: int = Field(default=6379)
    elastic_host: str = Field(default='elasticsearch')
    elastic_port: int = Field(default=9200)

    class Config:
        env_file = '.env'


app_settings = AppSettings()
