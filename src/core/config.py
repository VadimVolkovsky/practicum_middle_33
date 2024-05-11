import os
from logging import config as logging_config

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)
load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppSettings(BaseSettings):
    project_name: str = 'movies'
    redis_host: str = ...
    redis_port: int = ...
    elastic_host: str = Field(...,)
    elastic_port: int = Field(9200)

    class Config:
        env_file = '.env'


app_settings = AppSettings()
