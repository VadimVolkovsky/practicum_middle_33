from pydantic_settings import BaseSettings
from pydantic import Field


elastic_film_index_schema = {
    "settings": {
        "refresh_interval": "1s",
        "analysis": {
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"},
                "english_possessive_stemmer": {"type": "stemmer", "language": "possessive_english"},
                "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                "russian_stemmer": {"type": "stemmer", "language": "russian"}
            },
            "analyzer": {
                "ru_en": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "english_stop",
                        "english_stemmer",
                        "english_possessive_stemmer",
                        "russian_stop",
                        "russian_stemmer"
                    ]
                }
            }
        }
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "imdb_rating": {"type": "float"},
            "title": {
                "type": "text",
                "analyzer": "ru_en",
                "fields": {"raw": {"type": "keyword"}}
            },
            "description": {"type": "text", "analyzer": "ru_en"},
            "genre": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"}
                }
            },
            "directors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"}
                }
            },
            "actors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"}
                }
            },
            "writers": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {"id": {"type": "keyword"},
                               "name": {"type": "text", "analyzer": "ru_en"}
                               }
            }
        }
    }
}


class TestSettings(BaseSettings):
    # es_host: str = Field('elasticsearch:9200', env='ELASTIC_HOST')
    es_index: str = 'movies'
    es_id_field: str = 'test_es_id'  # какое это поле в эластике
    es_index_mapping: dict = elastic_film_index_schema

    # redis_host: str = 'redis'
    # service_url: str = 'http://api:8000'

    # для локального дебага тестов
    es_host: str = Field('127.0.0.1:9200', env='ELASTIC_HOST')
    redis_host: str = '127.0.0.1'
    service_url: str = 'http://127.0.0.1:8000'

    redis_port: int = 6379

test_settings = TestSettings()
